from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from accounts.models import UserProfile
from courses.models import Course, Subject
from teachers.models import Teacher, VolunteerWorkSession
from admin2.models import VolunteerAssignment


class InvigilatorModeTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # =====================================================
        # COURSE + SUBJECT
        # =====================================================

        self.course = Course.objects.create(
            name="Science"
        )

        self.subject = Subject.objects.create(
            name="Mathematics"
        )

        # =====================================================
        # ADMIN 2 USER
        # =====================================================

        self.admin2_user = User.objects.create_user(
            username="invigilator_admin2",
            email="invigilator_admin2@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin2_user,
            role="ADMIN2",
            is_active=True,
        )

        # =====================================================
        # VOLUNTEER USER
        # =====================================================

        self.volunteer_user = User.objects.create_user(
            username="invigilator_test@example.com",
            email="invigilator_test@example.com",
            password="VolunteerPassword123",
        )

        UserProfile.objects.create(
            user=self.volunteer_user,
            role="TEACHER_VOLUNTEER",
            is_active=True,
        )

        # =====================================================
        # VOLUNTEER
        # =====================================================

        self.volunteer = Teacher.objects.create(
            auth_user=self.volunteer_user,
            user_id="TESM901",
            name="Invigilator Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="invigilator_test@example.com",
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

        # =====================================================
        # AUTHENTICATE VOLUNTEER
        # =====================================================

        self.client.force_authenticate(
            user=self.volunteer_user
        )

    # =========================================================
    # HELPER
    # =========================================================

    def create_invigilator_assignment(
        self,
        email_status="SENT",
    ):
        return VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=timezone.localdate(),
            assigned_class="ClassA",
            task="INVIGILATOR",
            instruction="Monitor the examination hall.",
            email_status=email_status,
            created_by=self.admin2_user,
        )

    # =========================================================
    # NORMAL INVIGILATOR WORK MODE
    # =========================================================

    def test_invigilator_assignment_returns_invigilator_mode(self):
        assignment = self.create_invigilator_assignment()

        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["work_mode"]["code"],
            "INVIGILATOR",
        )

        self.assertEqual(
            data["work_mode"]["name"],
            "Invigilator",
        )

        self.assertEqual(
            data["assignment"]["id"],
            assignment.id,
        )

        self.assertEqual(
            data["assignment"]["assigned_class"],
            "ClassA",
        )

        self.assertEqual(
            data["assignment"]["task"],
            "INVIGILATOR",
        )

        self.assertEqual(
            data["work_source"],
            "ASSIGNED",
        )

    # =========================================================
    # SESSION START
    # =========================================================

    def test_invigilator_can_start_session(self):
        assignment = self.create_invigilator_assignment()

        response = self.client.post(
            "/api/teachers/session/start/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [200, 201],
        )

        session = VolunteerWorkSession.objects.get(
            assignment=assignment,
            volunteer=self.volunteer,
        )

        self.assertEqual(
            session.status,
            "IN_PROGRESS",
        )

        self.assertIsNotNone(
            session.started_at
        )

    # =========================================================
    # ACTIVE SESSION
    # =========================================================

    def test_invigilator_active_session_is_returned(self):
        assignment = self.create_invigilator_assignment()

        start_response = self.client.post(
            "/api/teachers/session/start/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertIn(
            start_response.status_code,
            [200, 201],
        )

        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["work_mode"]["code"],
            "INVIGILATOR",
        )

        self.assertEqual(
            data["work_session"]["status"],
            "IN_PROGRESS",
        )

        self.assertIsNotNone(
            data["work_session"]["started_at"]
        )

        self.assertGreaterEqual(
            data["work_session"]["elapsed_seconds"],
            0,
        )

    # =========================================================
    # SESSION END
    # =========================================================

    def test_invigilator_can_end_session(self):
        assignment = self.create_invigilator_assignment()

        start_response = self.client.post(
            "/api/teachers/session/start/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertIn(
            start_response.status_code,
            [200, 201],
        )

        end_response = self.client.post(
            "/api/teachers/session/end/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertEqual(
            end_response.status_code,
            200,
        )

        session = VolunteerWorkSession.objects.get(
            assignment=assignment,
            volunteer=self.volunteer,
        )

        self.assertEqual(
            session.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            session.started_at
        )

        self.assertIsNotNone(
            session.ended_at
        )

    # =========================================================
    # COMPLETED SESSION
    # =========================================================

    def test_completed_invigilator_session_is_returned(self):
        assignment = self.create_invigilator_assignment()

        start_response = self.client.post(
            "/api/teachers/session/start/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertIn(
            start_response.status_code,
            [200, 201],
        )

        end_response = self.client.post(
            "/api/teachers/session/end/",
            {
                "assignment": assignment.id,
            },
            format="json",
        )

        self.assertEqual(
            end_response.status_code,
            200,
        )

        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["work_mode"]["code"],
            "INVIGILATOR",
        )

        self.assertEqual(
            data["work_session"]["status"],
            "COMPLETED",
        )

        self.assertIsNotNone(
            data["work_session"]["started_at"]
        )

        self.assertIsNotNone(
            data["work_session"]["ended_at"]
        )

        self.assertGreaterEqual(
            data["work_session"]["elapsed_seconds"],
            0,
        )

    # =========================================================
    # UNSENT ASSIGNMENT
    # =========================================================

    def test_unsent_invigilator_assignment_is_not_active_work(self):
        self.create_invigilator_assignment(
            email_status="NOT_SENT"
        )

        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIsNone(
            data["work_mode"]
        )

        self.assertEqual(
            data["work_source"],
            "NONE",
        )

    # =========================================================
    # NO ASSIGNMENT
    # =========================================================

    def test_no_invigilator_assignment_returns_no_work(self):
        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIsNone(
            data["work_mode"]
        )

        self.assertEqual(
            data["work_source"],
            "NONE",
        )

        self.assertIsNone(
            data["assignment"]
        )

        self.assertIsNone(
            data["work_session"]
        )

    # =========================================================
    # INVIGILATOR HAS NO STUDENT-PROGRESS REQUIREMENT
    # =========================================================

    def test_invigilator_mode_does_not_require_student_progress(self):
        self.create_invigilator_assignment()

        response = self.client.get(
            "/api/teachers/work-mode/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["work_mode"]["code"],
            "INVIGILATOR",
        )

        # The Invigilator workflow only needs the work mode,
        # assignment and session. No student-progress data
        # is required by this endpoint.
        self.assertNotIn(
            "students",
            data,
        )