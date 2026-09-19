from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserProfile
from attendance.models import AttendanceSession, VolunteerAttendance, StudentAttendance
from admin2.models import VolunteerAssignment
from courses.models import Course, Subject
from students.models import Student, StudentHomework, StudentXPTransaction
from teachers.models import (
    Teacher,
    SpecialAddedWorkAccess,
    VolunteerWorkSession,
    StudentProgress,
)


class SpecialAddedWorkFlowTests(TestCase):
    """
    Dedicated end-to-end tests for the Special Added volunteer flow.

    Flow covered:

        Original volunteer -> ABSENT
        Special Added volunteer -> PRESENT
        Special Added selects original assignment
        Special Added starts/ends the selected work
        Special Added tracks student progress
        Homework is created as PENDING
        Homework completion awards +10 Student XP
    """

    def setUp(self):
        self.client = APIClient()

        # ============================================================
        # COURSE / SUBJECT
        # ============================================================

        self.course = Course.objects.create(
            name="Special Flow Science"
        )

        self.subject = Subject.objects.create(
            name="Special Flow Mathematics"
        )

        # ============================================================
        # ADMIN 1
        # ============================================================

        self.admin_user = User.objects.create_user(
            username="special_flow_admin",
            email="special_flow_admin@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin_user,
            role="ADMIN1",
            is_active=True,
        )

        # ============================================================
        # ORIGINAL VOLUNTEER
        # ============================================================

        self.original_user = User.objects.create_user(
            username="special_flow_original@example.com",
            email="special_flow_original@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.original_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        self.original = Teacher.objects.create(
            auth_user=self.original_user,
            user_id="SFO001",
            name="Original Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="special_flow_original@example.com",
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

        # ============================================================
        # SPECIAL ADDED VOLUNTEER
        # ============================================================

        self.special_user = User.objects.create_user(
            username="special_flow_special@example.com",
            email="special_flow_special@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.special_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        self.special = Teacher.objects.create(
            auth_user=self.special_user,
            user_id="SFS001",
            name="Special Added Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="special_flow_special@example.com",
            whatsapp_number="9876543211",
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

        self.today = timezone.localdate()

        # ============================================================
        # ORIGINAL ASSIGNMENT
        # ============================================================

        self.assignment = VolunteerAssignment.objects.create(
            volunteer=self.original,
            assignment_date=self.today,
            assigned_class="ClassA",
            task="TEACHING",
            instruction="Teach mathematics.",
            email_status="SENT",
            created_by=self.admin_user,
        )

        # ============================================================
        # ATTENDANCE SESSION
        # ============================================================

        self.attendance_session = AttendanceSession.objects.create(
            admin=self.admin_user,
            session_date=self.today,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.original,
            task="TEACHING",
            status="ABSENT",
            attendance_source="ASSIGNED",
        )

        self.special_attendance = VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.special,
            task="TEACHING",
            status="PRESENT",
            attendance_source="SPECIAL_ADDED",
        )

        # ============================================================
        # PRESENT STUDENT
        # ============================================================

        self.student = Student.objects.create(
            roll_no="JAA8S001",
            name="Special Flow Student",
            student_class="1",
            school_name="Jaago School",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.student,
            status="PRESENT",
        )

        # ============================================================
        # AUTHENTICATE AS SPECIAL ADDED VOLUNTEER
        # ============================================================

        self.client.force_authenticate(
            user=self.special_user
        )

    # ============================================================
    # HELPERS
    # ============================================================

    def select_work(self):
        response = self.client.post(
            "/api/teachers/special-added/select-work/",
            {
                "assignment": self.assignment.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content,
        )

        return SpecialAddedWorkAccess.objects.get(
            special_volunteer=self.special
        )

    def start_and_end_work(self):
        access = self.select_work()

        start_response = self.client.post(
            "/api/teachers/session/start/",
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            status.HTTP_200_OK,
            start_response.content,
        )

        session = VolunteerWorkSession.objects.get(
            assignment=self.assignment,
            volunteer=self.special,
        )

        self.assertEqual(
            session.status,
            "IN_PROGRESS",
        )

        end_response = self.client.post(
            "/api/teachers/session/end/",
            format="json",
        )

        self.assertEqual(
            end_response.status_code,
            status.HTTP_200_OK,
            end_response.content,
        )

        session.refresh_from_db()
        access.refresh_from_db()

        return access, session


    def start_work(self):
        access = self.select_work()

        start_response = self.client.post(
            "/api/teachers/session/start/",
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            status.HTTP_200_OK,
            start_response.content,
        )

        session = VolunteerWorkSession.objects.get(
            assignment=self.assignment,
            volunteer=self.special,
        )

        self.assertEqual(
            session.status,
            "IN_PROGRESS",
        )

        return access, session

    def end_work(self):
        end_response = self.client.post(
            "/api/teachers/session/end/",
            format="json",
        )

        self.assertEqual(
            end_response.status_code,
            status.HTTP_200_OK,
            end_response.content,
        )

        session = VolunteerWorkSession.objects.get(
            assignment=self.assignment,
            volunteer=self.special,
        )
        session.refresh_from_db()

        return session

    # ============================================================
    # WORK SESSION
    # ============================================================

    def test_special_added_selected_work_creates_session_for_special_volunteer(self):
        access, session = self.start_and_end_work()

        self.assertEqual(
            session.assignment,
            self.assignment,
        )

        self.assertEqual(
            session.volunteer,
            self.special,
        )

        self.assertEqual(
            self.assignment.volunteer,
            self.original,
        )

        self.assertEqual(
            access.assignment,
            self.assignment,
        )

        self.assertEqual(
            access.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            access.completed_at
        )

    # ============================================================
    # TRACK PROGRESS
    # ============================================================

    def test_special_added_can_track_progress_for_selected_assignment(self):
        self.start_work()

        response = self.client.get(
            "/api/teachers/students/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.content,
        )

        data = response.json()

        self.assertEqual(
            data["assignment"]["id"],
            self.assignment.id,
        )

        self.assertEqual(
            data["assignment"]["class"],
            "ClassA",
        )

        self.assertEqual(
            len(data["students"]),
            1,
        )

        self.assertEqual(
            data["students"][0]["student_id"],
            self.student.id,
        )

        self.assertEqual(
            data["students"][0]["attendance"],
            "PRESENT",
        )

    # ============================================================
    # SAVE PROGRESS + HOMEWORK
    # ============================================================

    def test_special_added_can_save_progress_and_create_pending_homework(self):
        self.start_work()

        response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "GOOD",
                "feedback": "Excellent participation.",
                "homework_given": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content,
        )

        progress = StudentProgress.objects.get(
            assignment=self.assignment,
            volunteer=self.special,
            student=self.student,
        )

        self.assertEqual(
            progress.work_session.volunteer,
            self.special,
        )

        self.assertEqual(
            progress.performance,
            "GOOD",
        )

        homework = StudentHomework.objects.get(
            student=self.student,
            assignment=self.assignment,
        )

        self.assertEqual(
            homework.status,
            "PENDING",
        )

        self.assertEqual(
            homework.work_session.volunteer,
            self.special,
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student
            ).count(),
            0,
        )

    # ============================================================
    # HOMEWORK COMPLETION + XP
    # ============================================================

    def test_special_added_can_complete_homework_and_award_ten_xp(self):
        self.start_work()

        save_response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "GOOD",
                "feedback": "Homework assigned.",
                "homework_given": True,
            },
            format="json",
        )

        self.assertEqual(
            save_response.status_code,
            status.HTTP_201_CREATED,
            save_response.content,
        )

        homework_id = save_response.json()["homework"]["id"]

        # Homework completion is allowed only after the volunteer
        # work session has ended.
        self.end_work()

        complete_response = self.client.post(
            f"/api/students/homework/{homework_id}/complete/",
            format="json",
        )

        self.assertEqual(
            complete_response.status_code,
            status.HTTP_200_OK,
            complete_response.content,
        )

        self.assertEqual(
            complete_response.json()["xp_awarded"],
            10,
        )

        homework = StudentHomework.objects.get(
            id=homework_id
        )

        self.assertEqual(
            homework.status,
            "COMPLETED",
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student,
                homework=homework,
            ).count(),
            1,
        )

    # ============================================================
    # SECURITY: WRONG GROUP
    # ============================================================

    def test_special_added_cannot_save_progress_for_wrong_group(self):
        self.start_work()

        wrong_student = Student.objects.create(
            roll_no="JAA8S002",
            name="Wrong Group Student",
            student_class="4",
            school_name="Jaago School",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=wrong_student,
            status="PRESENT",
        )

        response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": wrong_student.id,
                "performance": "GOOD",
                "feedback": "Should be rejected.",
                "homework_given": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            response.json()["code"],
            "STUDENT_CLASS_MISMATCH",
        )

        self.assertFalse(
            StudentProgress.objects.filter(
                assignment=self.assignment,
                volunteer=self.special,
                student=wrong_student,
            ).exists()
        )

        self.assertFalse(
            StudentHomework.objects.filter(
                assignment=self.assignment,
                student=wrong_student,
            ).exists()
        )
