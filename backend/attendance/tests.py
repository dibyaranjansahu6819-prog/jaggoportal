from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from accounts.models import UserProfile
from courses.models import Course, Subject
from students.models import Student
from teachers.models import Teacher

from .models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
)


class AttendanceBackendTests(TestCase):
    """
    Tests for the current Jaago Portal attendance backend.

    Covers:

    - Admin 1 authentication/permissions
    - 10-minute attendance sessions
    - Student attendance
    - Volunteer attendance
    - Teaching / Checking tasks
    - ASSIGNED attendance
    - SPECIAL_ADDED attendance
    - Removed volunteer protection
    - Today's attendance data
    - Attendance history
    """

    def setUp(self):
        self.client = APIClient()

        # =========================================================
        # COURSE
        # =========================================================

        self.course = Course.objects.create(
            name="Science"
        )

        # =========================================================
        # SUBJECT
        # =========================================================

        self.subject = Subject.objects.create(
            name="Mathematics"
        )

        # =========================================================
        # ADMIN 1 USER
        # =========================================================

        self.admin1_user = User.objects.create_user(
            username="admin1_test",
            email="admin1@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin1_user,
            role="ADMIN1",
            is_active=True,
        )

        # =========================================================
        # STUDENT
        # =========================================================

        self.student = Student.objects.create(
            roll_no="JAA901",
            name="Test Student",
            student_class="9",
            school_name="Jaago School",
        )

        # =========================================================
        # VOLUNTEER AUTH USER
        # =========================================================

        self.volunteer_user = User.objects.create_user(
            username="volunteer@example.com",
            email="volunteer@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.volunteer_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        # =========================================================
        # VOLUNTEER
        # =========================================================

        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="TESM001",
            name="Test Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="volunteer@example.com",
            whatsapp_number="9876543210",
            free_days=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ],
            password="",
        )

        # =========================================================
        # AUTHENTICATE AS ADMIN 1
        # =========================================================

        self.client.force_authenticate(
            user=self.admin1_user
        )

    # =========================================================
    # ATTENDANCE SESSION TESTS
    # =========================================================

    def test_admin1_can_start_attendance_session(self):
        response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            AttendanceSession.objects.filter(
                admin=self.admin1_user,
                is_active=True,
            ).exists()
        )

    def test_attendance_session_is_ten_minutes(self):
        response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        session = AttendanceSession.objects.get(
            admin=self.admin1_user
        )

        difference = (
            session.expires_at - session.started_at
        )

        # started_at uses auto_now_add while expires_at is
        # calculated using timezone.now(), so a tiny
        # microsecond difference is expected.
        self.assertAlmostEqual(
            difference.total_seconds(),
            600,
            delta=1,
        )

    def test_only_one_active_session_exists(self):
        first_response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertEqual(
            AttendanceSession.objects.filter(
                is_active=True
            ).count(),
            1,
        )

    def test_current_session_returns_active_session(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/session/current/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIsNotNone(
            data["session"]
        )

    def test_admin1_can_end_attendance_session(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/session/end/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        session = AttendanceSession.objects.get(
            admin=self.admin1_user
        )

        self.assertFalse(
            session.is_active
        )

        self.assertIsNotNone(
            session.ended_at
        )

    # =========================================================
    # STUDENT ATTENDANCE
    # =========================================================

    def test_student_attendance_defaults_to_absent(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/students/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            len(data["students"]),
            1,
        )

        self.assertEqual(
            data["students"][0]["status"],
            "ABSENT",
        )

    def test_student_attendance_can_be_marked_present(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/students/save/",
            {
                "student": self.student.id,
                "status": "PRESENT",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        attendance = StudentAttendance.objects.get(
            student=self.student
        )

        self.assertEqual(
            attendance.status,
            "PRESENT",
        )

    def test_student_attendance_can_be_changed_to_absent(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        self.client.post(
            "/api/attendance/students/save/",
            {
                "student": self.student.id,
                "status": "PRESENT",
            },
            format="json",
        )

        response = self.client.post(
            "/api/attendance/students/save/",
            {
                "student": self.student.id,
                "status": "ABSENT",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        attendance = StudentAttendance.objects.get(
            student=self.student
        )

        self.assertEqual(
            attendance.status,
            "ABSENT",
        )

    def test_invalid_student_status_is_rejected(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/students/save/",
            {
                "student": self.student.id,
                "status": "INVALID",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================================
    # VOLUNTEER ATTENDANCE
    # =========================================================

    def test_assigned_volunteer_is_not_added_without_assignment(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/volunteers/current/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["volunteers"],
            [],
        )

    def test_special_added_volunteer_can_be_added(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        attendance = VolunteerAttendance.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            attendance.task,
            "TEACHING",
        )

        self.assertEqual(
            attendance.attendance_source,
            "SPECIAL_ADDED",
        )

        self.assertEqual(
            attendance.status,
            "ABSENT",
        )

    def test_special_added_checking_task_is_saved(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "CHECKING",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        attendance = VolunteerAttendance.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            attendance.task,
            "CHECKING",
        )

        self.assertEqual(
            attendance.attendance_source,
            "SPECIAL_ADDED",
        )

    def test_volunteer_attendance_can_be_marked_present(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        response = self.client.post(
            "/api/attendance/volunteers/save/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
                "status": "PRESENT",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        attendance = VolunteerAttendance.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            attendance.status,
            "PRESENT",
        )

        self.assertEqual(
            attendance.attendance_source,
            "SPECIAL_ADDED",
        )

    def test_volunteer_attendance_source_is_preserved(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "CHECKING",
            },
            format="json",
        )

        self.client.post(
            "/api/attendance/volunteers/save/",
            {
                "volunteer": self.volunteer.id,
                "task": "CHECKING",
                "status": "PRESENT",
            },
            format="json",
        )

        attendance = VolunteerAttendance.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            attendance.attendance_source,
            "SPECIAL_ADDED",
        )

    def test_duplicate_volunteer_cannot_be_added(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        first_response = self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "CHECKING",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

    def test_removed_volunteer_cannot_be_added(self):
        """
        A volunteer removed by Admin 2 must not be allowed
        to be added manually by Admin 1.
        """

        from admin2.models import VolunteerAccountStatus

        # Mark volunteer as REMOVED
        VolunteerAccountStatus.objects.create(
            volunteer=self.volunteer,
            status="REMOVED",
        )

        # Start Admin 1 attendance session
        session_response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertIn(
            session_response.status_code,
            [200, 201],
        )

        # Try to manually add the removed volunteer
        response = self.client.post(
            "/api/attendance/volunteers/add/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        # Must be forbidden
        self.assertEqual(
            response.status_code,
            403,
        )

        # Must return the correct error code
        self.assertEqual(
            response.json()["code"],
            "VOLUNTEER_REMOVED",
        )

        # No attendance record should have been created
        self.assertFalse(
            VolunteerAttendance.objects.filter(
                volunteer=self.volunteer
            ).exists()
        )

    # =========================================================
    # ADMIN 2 ASSIGNMENT → ADMIN 1 ATTENDANCE
    # =========================================================

    def test_admin2_assignment_creates_teaching_attendance(self):
        """
        Admin 2 assigns TEACHING.
        Admin 1 attendance must show TEACHING.
        """

        from admin2.models import VolunteerAssignment

        assignment_date = timezone.localdate()

        self.volunteer.free_days = [
            assignment_date.strftime("%A")
        ]

        self.volunteer.save(
            update_fields=["free_days"]
        )

        VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=assignment_date,
            assigned_class="ClassA",
            task="TEACHING",
            instruction="Teach mathematics.",
            email_status="SENT",
            created_by=self.admin1_user,
        )

        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/volunteers/current/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        attendance = VolunteerAttendance.objects.get(
            session__admin=self.admin1_user,
            volunteer=self.volunteer,
        )

        self.assertEqual(
            attendance.task,
            "TEACHING",
        )

        self.assertEqual(
            attendance.attendance_source,
            "ASSIGNED",
        )

    def test_admin2_assignment_creates_checking_attendance(self):
        """
        Admin 2 assigns CHECKING.
        Admin 1 attendance must show CHECKING.
        """

        from admin2.models import VolunteerAssignment

        assignment_date = timezone.localdate()

        self.volunteer.free_days = [
            assignment_date.strftime("%A")
        ]

        self.volunteer.save(
            update_fields=["free_days"]
        )

        VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=assignment_date,
            assigned_class="ClassB",
            task="CHECKING",
            instruction="Check answer sheets.",
            email_status="SENT",
            created_by=self.admin1_user,
        )

        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/volunteers/current/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        attendance = VolunteerAttendance.objects.get(
            session__admin=self.admin1_user,
            volunteer=self.volunteer,
        )

        self.assertEqual(
            attendance.task,
            "CHECKING",
        )

        self.assertEqual(
            attendance.attendance_source,
            "ASSIGNED",
        )

    def test_unsent_assignment_does_not_create_assigned_attendance(self):
        from admin2.models import VolunteerAssignment

        assignment_date = timezone.localdate()

        self.volunteer.free_days = [
            assignment_date.strftime("%A")
        ]

        self.volunteer.save(
            update_fields=["free_days"]
        )

        VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=assignment_date,
            assigned_class="ClassA",
            task="TEACHING",
            instruction="Test assignment.",
            email_status="NOT_SENT",
            created_by=self.admin1_user,
        )

        self.client.post(
            "/api/attendance/session/start/"
        )

        self.client.get(
            "/api/attendance/volunteers/current/"
        )

        self.assertFalse(
            VolunteerAttendance.objects.filter(
                volunteer=self.volunteer
            ).exists()
        )

    # =========================================================
    # ACCESS WORK SUBSTITUTE / PLAYING DAY
    # =========================================================

    def test_playing_day_requires_playing_day_status(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/volunteers/add-playing-day/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_playing_day_volunteer_can_be_added(self):
        from admin2.models import DailySchoolStatus

        DailySchoolStatus.objects.create(
            date=timezone.localdate(),
            status="PLAYING_DAY",
            created_by=self.admin1_user,
        )

        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.post(
            "/api/attendance/volunteers/add-playing-day/",
            {
                "volunteer": self.volunteer.id,
                "task": "TEACHING",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        attendance = VolunteerAttendance.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            attendance.attendance_source,
            "PLAYING_DAY",
        )

        self.assertEqual(
            attendance.status,
            "ABSENT",
        )

    # =========================================================
    # VOLUNTEER LIST
    # =========================================================

    def test_volunteer_list_returns_registered_volunteers(self):
        response = self.client.get(
            "/api/attendance/volunteers/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "volunteers",
            data,
        )

        self.assertEqual(
            len(data["volunteers"]),
            1,
        )

        self.assertEqual(
            data["volunteers"][0]["id"],
            self.volunteer.id,
        )

    # =========================================================
    # TODAY SUMMARY
    # =========================================================

    def test_today_summary_returns_session_data(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/summary/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "date",
            data,
        )

        self.assertIn(
            "session",
            data,
        )

        self.assertIn(
            "students",
            data,
        )

        self.assertIn(
            "volunteers",
            data,
        )

    # =========================================================
    # ATTENDANCE HISTORY
    # =========================================================

    def test_attendance_history_returns_sessions(self):
        self.client.post(
            "/api/attendance/session/start/"
        )

        response = self.client.get(
            "/api/attendance/history/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "sessions",
            data,
        )

        self.assertEqual(
            len(data["sessions"]),
            1,
        )

    # =========================================================
    # PERMISSION TEST
    # =========================================================

    def test_unauthenticated_user_cannot_start_session(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/attendance/session/start/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )