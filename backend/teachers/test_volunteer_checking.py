from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import UserProfile
from attendance.models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
)
from admin2.models import VolunteerAssignment
from courses.models import Course, Subject
from students.models import Student, StudentHomework
from teachers.models import (
    Teacher,
    VolunteerWorkSession,
    StudentProgress,
    StudentChecking,
)


class VolunteerCheckingTests(TestCase):
    """
    Tests the complete normal Checking workflow:

        Login/authenticated volunteer
            ->
        Checking assignment
            ->
        Start session
            ->
        Present students
            ->
        Open student
            ->
        Save DONE / NOT_DONE + feedback
            ->
        Verify StudentChecking
            ->
        Verify Teaching performance is unchanged
            ->
        Update checking
            ->
        End session
    """

    def setUp(self):
        self.client = APIClient()

        # ========================================================
        # COURSE / SUBJECT
        # ========================================================

        self.course = Course.objects.create(
            name="Checking Science"
        )

        self.subject = Subject.objects.create(
            name="Checking Mathematics"
        )

        # ========================================================
        # ADMIN
        # ========================================================

        self.admin_user = User.objects.create_user(
            username="checking_admin",
            email="checking_admin@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin_user,
            role="ADMIN1",
            is_active=True,
        )

        # ========================================================
        # VOLUNTEER
        # ========================================================

        self.volunteer_user = User.objects.create_user(
            username="checking_volunteer@example.com",
            email="checking_volunteer@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.volunteer_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="CHECK001",
            name="Checking Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="checking_volunteer@example.com",
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

        # ========================================================
        # TODAY
        # ========================================================

        self.today = timezone.localdate()

        # ========================================================
        # CHECKING ASSIGNMENT
        # ========================================================

        self.assignment = VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=self.today,
            assigned_class="ClassA",
            task="CHECKING",
            instruction="Check today's student homework.",
            email_status="SENT",
            created_by=self.admin_user,
        )

        # ========================================================
        # ATTENDANCE SESSION
        # ========================================================

        self.attendance_session = AttendanceSession.objects.create(
            admin=self.admin_user,
            session_date=self.today,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        # Volunteer PRESENT for Checking
        VolunteerAttendance.objects.create(
            session=self.attendance_session,
            volunteer=self.volunteer,
            task="CHECKING",
            status="PRESENT",
            attendance_source="ASSIGNED",
        )

        # ========================================================
        # PRESENT STUDENTS
        # ========================================================

        self.student = Student.objects.create(
            roll_no="JAA1001",
            name="Checking Student",
            student_class="2",
            school_name="Jaago School",
        )

        self.second_student = Student.objects.create(
            roll_no="JAA1002",
            name="Second Checking Student",
            student_class="3",
            school_name="Jaago School",
        )

        # Wrong group student
        self.wrong_group_student = Student.objects.create(
            roll_no="JAA1003",
            name="Wrong Group Student",
            student_class="4",
            school_name="Jaago School",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.student,
            status="PRESENT",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.second_student,
            status="PRESENT",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.wrong_group_student,
            status="PRESENT",
        )

        # ========================================================
        # AUTHENTICATE
        # ========================================================

        self.client.force_authenticate(
            user=self.volunteer_user
        )

    # ============================================================
    # HELPER
    # ============================================================

    def start_checking_session(self):
        response = self.client.post(
            "/api/teachers/session/start/",
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.content,
        )

        session = VolunteerWorkSession.objects.get(
            assignment=self.assignment,
            volunteer=self.volunteer,
        )

        self.assertEqual(
            session.status,
            "IN_PROGRESS",
        )

        return session

    def create_homework(self, student, work_session):
        return StudentHomework.objects.create(
            student=student,
            assignment=self.assignment,
            work_session=work_session,
            status="PENDING",
        )

    # ============================================================
    # TEST 1
    # ============================================================

    def test_checking_dashboard_returns_present_students(self):
        self.start_checking_session()

        response = self.client.get(
            "/api/teachers/checking/"
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
            data["assignment"]["task"],
            "CHECKING",
        )

        self.assertEqual(
            data["assignment"]["assigned_class"],
            "ClassA",
        )

        self.assertEqual(
            data["students_present"],
            2,
        )

        self.assertEqual(
            data["students_checked"],
            0,
        )

        self.assertEqual(
            data["students_pending"],
            2,
        )

        student_ids = {
            item["student"]
            for item in data["students"]
        }

        self.assertIn(
            self.student.id,
            student_ids,
        )

        self.assertIn(
            self.second_student.id,
            student_ids,
        )

        self.assertNotIn(
            self.wrong_group_student.id,
            student_ids,
        )

    # ============================================================
    # TEST 2
    # ============================================================

    def test_checking_student_detail_requires_present_student(self):
        self.start_checking_session()

        response = self.client.get(
            f"/api/teachers/checking/students/{self.student.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.content,
        )

        data = response.json()

        self.assertEqual(
            data["student"]["id"],
            self.student.id,
        )

        self.assertEqual(
            data["student"]["roll_no"],
            self.student.roll_no,
        )

        self.assertEqual(
            data["attendance"]["status"],
            "PRESENT",
        )

        self.assertFalse(
            data["checked"]
        )

        self.assertIsNone(
            data["checking"]
        )

    # ============================================================
    # TEST 3
    # ============================================================

    def test_checking_save_requires_homework(self):
        self.start_checking_session()

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Good work.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )

        self.assertEqual(
            response.json()["code"],
            "NO_HOMEWORK",
        )

        self.assertFalse(
            StudentChecking.objects.filter(
                assignment=self.assignment,
                student=self.student,
            ).exists()
        )

    # ============================================================
    # TEST 4
    # ============================================================

    def test_checking_save_done_creates_student_checking(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Good work. Keep improving.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content,
        )

        checking = StudentChecking.objects.get(
            assignment=self.assignment,
            volunteer=self.volunteer,
            student=self.student,
        )

        self.assertEqual(
            checking.homework_status,
            "DONE",
        )

        self.assertEqual(
            checking.feedback,
            "Good work. Keep improving.",
        )

        self.assertEqual(
            checking.work_session,
            work_session,
        )

    # ============================================================
    # TEST 5
    # ============================================================

    def test_checking_save_not_done_works(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.second_student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.second_student.id}/save/",
            {
                "homework_status": "NOT_DONE",
                "feedback": "Homework was not completed.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content,
        )

        checking = StudentChecking.objects.get(
            assignment=self.assignment,
            volunteer=self.volunteer,
            student=self.second_student,
        )

        self.assertEqual(
            checking.homework_status,
            "NOT_DONE",
        )

        self.assertEqual(
            checking.feedback,
            "Homework was not completed.",
        )

    # ============================================================
    # TEST 6
    # ============================================================

    def test_checking_can_update_existing_record(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
        )

        first_response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "NOT_DONE",
                "feedback": "Not completed.",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )

        second_response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Completed after correction.",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
            second_response.content,
        )

        self.assertEqual(
            StudentChecking.objects.filter(
                assignment=self.assignment,
                volunteer=self.volunteer,
                student=self.student,
            ).count(),
            1,
        )

        checking = StudentChecking.objects.get(
            assignment=self.assignment,
            volunteer=self.volunteer,
            student=self.student,
        )

        self.assertEqual(
            checking.homework_status,
            "DONE",
        )

        self.assertEqual(
            checking.feedback,
            "Completed after correction.",
        )

    # ============================================================
    # TEST 7
    # ============================================================

    def test_checking_cannot_save_before_session_starts(self):
        work_session = VolunteerWorkSession.objects.create(
            assignment=self.assignment,
            volunteer=self.volunteer,
            status="NOT_STARTED",
        )

        self.create_homework(
            self.student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Should not save.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )

        self.assertEqual(
            response.json()["code"],
            "WORK_SESSION_NOT_ACTIVE",
        )

        self.assertFalse(
            StudentChecking.objects.filter(
                assignment=self.assignment,
                student=self.student,
            ).exists()
        )

    # ============================================================
    # TEST 8
    # ============================================================

    def test_checking_cannot_save_for_wrong_group(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.wrong_group_student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.wrong_group_student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Wrong group.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )

        self.assertEqual(
            response.json()["code"],
            "STUDENT_NOT_PRESENT",
        )

        self.assertFalse(
            StudentChecking.objects.filter(
                assignment=self.assignment,
                student=self.wrong_group_student,
            ).exists()
        )

    # ============================================================
    # TEST 9
    # ============================================================

    def test_checking_does_not_modify_teaching_performance(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
        )

        # Existing Teaching record.
        progress = StudentProgress.objects.create(
            assignment=self.assignment,
            work_session=work_session,
            volunteer=self.volunteer,
            student=self.student,
            performance="GOOD",
            feedback="Teaching feedback.",
            homework_given=True,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "NOT_DONE",
                "feedback": "Checking feedback.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content,
        )

        progress.refresh_from_db()

        self.assertEqual(
            progress.performance,
            "GOOD",
        )

        self.assertEqual(
            progress.feedback,
            "Teaching feedback.",
        )

        checking = StudentChecking.objects.get(
            assignment=self.assignment,
            student=self.student,
        )

        self.assertEqual(
            checking.homework_status,
            "NOT_DONE",
        )

        self.assertEqual(
            checking.feedback,
            "Checking feedback.",
        )

    # ============================================================
    # TEST 10
    # ============================================================

    def test_checking_cannot_save_after_session_ends(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
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

        work_session.refresh_from_db()

        self.assertEqual(
            work_session.status,
            "COMPLETED",
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Too late.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )

        self.assertEqual(
            response.json()["code"],
            "WORK_SESSION_NOT_ACTIVE",
        )

    # ============================================================
    # TEST 11
    # ============================================================

    def test_checking_dashboard_updates_checked_counter(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
        )

        self.create_homework(
            self.second_student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "DONE",
                "feedback": "Checked.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        dashboard_response = self.client.get(
            "/api/teachers/checking/"
        )

        self.assertEqual(
            dashboard_response.status_code,
            status.HTTP_200_OK,
        )

        data = dashboard_response.json()

        self.assertEqual(
            data["students_present"],
            2,
        )

        self.assertEqual(
            data["students_checked"],
            1,
        )

        self.assertEqual(
            data["students_pending"],
            1,
        )

    # ============================================================
    # TEST 12
    # ============================================================

    def test_checking_rejects_invalid_homework_status(self):
        work_session = self.start_checking_session()

        self.create_homework(
            self.student,
            work_session,
        )

        response = self.client.post(
            f"/api/teachers/checking/students/{self.student.id}/save/",
            {
                "homework_status": "PENDING",
                "feedback": "Invalid status.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )

        self.assertEqual(
            response.json()["code"],
            "INVALID_HOMEWORK_STATUS",
        )

        self.assertFalse(
            StudentChecking.objects.filter(
                assignment=self.assignment,
                student=self.student,
            ).exists()
        )