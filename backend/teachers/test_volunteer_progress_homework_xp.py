from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from attendance.models import AttendanceSession, StudentAttendance
from admin2.models import VolunteerAssignment
from students.models import Student, StudentHomework, StudentXPTransaction
from teachers.models import Teacher, VolunteerWorkSession, StudentProgress
from courses.models import Course, Subject


class VolunteerProgressHomeworkFlowTests(APITestCase):
    """
    End-to-end tests for:

    PRESENT student
        -> Volunteer Progress
        -> Homework Given
        -> Homework COMPLETED
        -> +10 Student XP
    """

    def setUp(self):
        self.course = Course.objects.create(name="Science")
        self.subject = Subject.objects.create(name="Mathematics")

        self.volunteer_user = User.objects.create_user(
            username="progressvolunteer@example.com",
            email="progressvolunteer@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.volunteer_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="PROGVOL001",
            name="Progress Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="progressvolunteer@example.com",
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

        self.student = Student.objects.create(
            roll_no="JAA0235",
            name="Class Two Student",
            student_class="2",
            school_name="Jaago School",
        )

        # Class 4 belongs to ClassB and must not appear in a ClassA assignment.
        self.other_group_student = Student.objects.create(
            roll_no="JAA0436",
            name="Class Four Student",
            student_class="4",
            school_name="Jaago School",
        )

        self.assignment = VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=timezone.localdate(),
            assigned_class="ClassA",
            task="TEACHING",
            instruction="Teach mathematics and give homework.",
            email_status="SENT",
            created_by=self.volunteer_user,
        )

        self.work_session = VolunteerWorkSession.objects.create(
            assignment=self.assignment,
            volunteer=self.volunteer,
            status="IN_PROGRESS",
            started_at=timezone.now() - timedelta(minutes=30),
            ended_at=None,
            total_seconds=0,
        )

        self.attendance_session = AttendanceSession.objects.create(
            admin=self.volunteer_user,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.student,
            status="PRESENT",
        )

        StudentAttendance.objects.create(
            session=self.attendance_session,
            student=self.other_group_student,
            status="PRESENT",
        )

        self.client.force_authenticate(
            user=self.volunteer_user
        )

    def complete_work_session(self):
        self.work_session.status = "COMPLETED"
        self.work_session.ended_at = timezone.now()
        self.work_session.total_seconds = 1800
        self.work_session.save(
            update_fields=["status", "ended_at", "total_seconds"]
        )

    def test_progress_students_returns_only_present_students_in_assigned_group(self):
        response = self.client.get(
            "/api/teachers/students/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        data = response.json()

        self.assertEqual(
            len(data["students"]),
            1,
        )

        self.assertEqual(
            data["students"][0]["student_id"],
            self.student.id,
        )

        self.assertEqual(
            data["students"][0]["class"],
            "2",
        )

        self.assertEqual(
            self.student.group,
            "ClassA",
        )

        self.assertEqual(
            self.other_group_student.group,
            "ClassB",
        )

    def test_progress_save_with_homework_given_creates_pending_homework(self):
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
            homework.work_session_id,
            self.work_session.id,
        )

        self.assertIsNone(
            homework.completed_at
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student
            ).count(),
            0,
        )

        self.assertIsNotNone(
            response.json()["homework"]
        )

    def test_pending_homework_gives_zero_xp_before_completion(self):
        self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "AVERAGE",
                "feedback": "Needs more practice.",
                "homework_given": True,
            },
            format="json",
        )

        response = self.client.get(
            f"/api/students/{self.student.id}/xp/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json()["total_xp"],
            0,
        )

    def test_homework_completion_awards_exactly_ten_xp(self):
        save_response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "GOOD",
                "feedback": "Good work.",
                "homework_given": True,
            },
            format="json",
        )

        homework_id = save_response.json()["homework"]["id"]

        self.complete_work_session()

        response = self.client.post(
            f"/api/students/homework/{homework_id}/complete/",
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json()["xp_awarded"],
            10,
        )

        homework = StudentHomework.objects.get(
            id=homework_id
        )

        self.assertEqual(
            homework.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            homework.completed_at
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student,
                homework=homework,
            ).count(),
            1,
        )

        xp_response = self.client.get(
            f"/api/students/{self.student.id}/xp/"
        )

        self.assertEqual(
            xp_response.json()["total_xp"],
            10,
        )

    def test_completing_same_homework_twice_does_not_award_extra_xp(self):
        save_response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "GOOD",
                "feedback": "Complete the assigned work.",
                "homework_given": True,
            },
            format="json",
        )

        homework_id = save_response.json()["homework"]["id"]

        self.complete_work_session()

        first_response = self.client.post(
            f"/api/students/homework/{homework_id}/complete/",
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            f"/api/students/homework/{homework_id}/complete/",
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            second_response.json()["xp_awarded"],
            0,
        )

        self.assertEqual(
            StudentXPTransaction.objects.filter(
                student=self.student
            ).count(),
            1,
        )

        xp_response = self.client.get(
            f"/api/students/{self.student.id}/xp/"
        )

        self.assertEqual(
            xp_response.json()["total_xp"],
            10,
        )

    def test_progress_is_rejected_after_session_is_completed(self):
        self.work_session.status = "COMPLETED"
        self.work_session.ended_at = timezone.now()
        self.work_session.total_seconds = 1800
        self.work_session.save(
            update_fields=["status", "ended_at", "total_seconds"]
        )

        response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.student.id,
                "performance": "GOOD",
                "feedback": "Session already ended.",
                "homework_given": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("active", response.json()["error"].lower())

        self.assertFalse(
            StudentProgress.objects.filter(
                student=self.student,
                assignment=self.assignment,
            ).exists()
        )

    def test_progress_students_is_rejected_after_session_is_completed(self):
        self.work_session.status = "COMPLETED"
        self.work_session.ended_at = timezone.now()
        self.work_session.total_seconds = 1800
        self.work_session.save(
            update_fields=["status", "ended_at", "total_seconds"]
        )

        response = self.client.get("/api/teachers/students/")

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            response.json()["work_session_status"],
            "COMPLETED",
        )

    def test_progress_save_for_wrong_group_is_rejected(self):
        response = self.client.post(
            "/api/teachers/progress/",
            {
                "student": self.other_group_student.id,
                "performance": "GOOD",
                "feedback": "Wrong group test.",
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
                student=self.other_group_student,
                assignment=self.assignment,
            ).exists()
        )

        self.assertFalse(
            StudentHomework.objects.filter(
                student=self.other_group_student,
                assignment=self.assignment,
            ).exists()
        )
