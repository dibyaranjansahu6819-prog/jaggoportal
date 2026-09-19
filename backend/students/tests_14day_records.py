from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from attendance.models import (
    AttendanceSession,
    Holiday,
    StudentAttendance,
)
from admin2.models import VolunteerAssignment
from courses.models import Course, Subject
from teachers.models import Teacher, VolunteerWorkSession
from .models import Student, StudentHomework, StudentXPTransaction


class Student14DayHistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="history@example.com",
            password="HistoryPassword123",
        )
        self.client.force_authenticate(user=self.user)

        self.student = Student.objects.create(
            roll_no="JAA0914",
            name="History Student",
            student_class="9",
            group="ClassD",
            school_name="Jaago School",
        )

        self.course = Course.objects.create(name="History Course")
        self.subject = Subject.objects.create(name="Mathematics")

        self.volunteer_user = User.objects.create_user(
            username="historyvol@example.com",
            password="VolunteerPassword123",
        )

        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="HIST001",
            name="History Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="historyvol@example.com",
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

    def create_session_with_attendance(self, date_value, attendance_status):
        session = AttendanceSession.objects.create(
            admin=self.user,
            session_date=date_value,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        StudentAttendance.objects.create(
            session=session,
            student=self.student,
            status=attendance_status,
        )

        return session

    def create_homework(self, date_value, completed=False):
        assignment = VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=date_value,
            assigned_class="ClassD",
            task="TEACHING",
            instruction="History homework",
            email_status="SENT",
            created_by=self.volunteer_user,
        )

        work_session = VolunteerWorkSession.objects.create(
            assignment=assignment,
            volunteer=self.volunteer,
            status="COMPLETED",
            started_at=timezone.now(),
            ended_at=timezone.now(),
            total_seconds=600,
        )

        homework = StudentHomework.objects.create(
            student=self.student,
            assignment=assignment,
            work_session=work_session,
            status="COMPLETED" if completed else "PENDING",
            completed_at=timezone.now() if completed else None,
        )

        if completed:
            StudentXPTransaction.objects.create(
                student=self.student,
                points=10,
                source="HOMEWORK_COMPLETED",
                reason="Homework completed",
                homework=homework,
                created_by=None,
            )

        return homework

    def test_returns_exactly_14_calendar_days(self):
        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data["records"]),
            14,
        )
        self.assertEqual(
            response.data["period"]["days"],
            14,
        )

    def test_today_and_start_dates_are_correct(self):
        today = timezone.localdate()

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["period"]["start_date"],
            str(today - timedelta(days=13)),
        )
        self.assertEqual(
            response.data["period"]["end_date"],
            str(today),
        )

    def test_present_and_absent_are_reported(self):
        today = timezone.localdate()

        self.create_session_with_attendance(
            today,
            "PRESENT",
        )
        self.create_session_with_attendance(
            today - timedelta(days=1),
            "ABSENT",
        )

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        records = {
            item["date"]: item
            for item in response.data["records"]
        }

        self.assertEqual(
            records[str(today)]["attendance_status"],
            "PRESENT",
        )
        self.assertEqual(
            records[str(today - timedelta(days=1))]["attendance_status"],
            "ABSENT",
        )

    def test_holiday_is_not_treated_as_absent(self):
        today = timezone.localdate()

        Holiday.objects.create(
            date=today - timedelta(days=2),
            name="School Holiday",
            created_by=self.user,
            is_active=True,
        )

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        records = {
            item["date"]: item
            for item in response.data["records"]
        }

        holiday_record = records[
            str(today - timedelta(days=2))
        ]

        self.assertEqual(
            holiday_record["attendance_status"],
            "HOLIDAY",
        )
        self.assertEqual(
            holiday_record["holiday_name"],
            "School Holiday",
        )

    def test_no_session_is_no_record(self):
        today = timezone.localdate()

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        records = {
            item["date"]: item
            for item in response.data["records"]
        }

        self.assertEqual(
            records[str(today)]["attendance_status"],
            "NO_RECORD",
        )

    def test_homework_counts_and_xp_are_reported(self):
        today = timezone.localdate()

        self.create_homework(today, completed=True)
        self.create_homework(
            today - timedelta(days=1),
            completed=False,
        )

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        records = {
            item["date"]: item
            for item in response.data["records"]
        }

        today_record = records[str(today)]
        yesterday_record = records[
            str(today - timedelta(days=1))
        ]

        self.assertEqual(today_record["homework_total"], 1)
        self.assertEqual(today_record["homework_completed"], 1)
        self.assertEqual(today_record["homework_pending"], 0)
        self.assertEqual(today_record["homework_xp"], 10)
        self.assertEqual(today_record["total_xp_earned"], 10)

        self.assertEqual(yesterday_record["homework_total"], 1)
        self.assertEqual(yesterday_record["homework_completed"], 0)
        self.assertEqual(yesterday_record["homework_pending"], 1)
        self.assertEqual(yesterday_record["homework_xp"], 0)

    def test_student_not_found(self):
        response = self.client.get(
            "/api/students/999999/14-day-history/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            f"/api/students/{self.student.id}/14-day-history/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
