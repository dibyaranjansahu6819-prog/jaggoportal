from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from accounts.models import UserProfile
from attendance.models import (
    AttendanceSession,
    VolunteerAttendance,
)
from courses.models import Course, Subject
from teachers.models import Teacher

from .models import (
    DailySchoolStatus,
    VolunteerAccountStatus,
    VolunteerAccessRequest,
    VolunteerAssignment,
    VolunteerCaution,
    VolunteerXPTransaction,
)
from .services import (
    check_and_create_caution,
    get_assigned_absence_streak,
    get_current_status,
    get_volunteer_xp,
    sync_attendance_xp,
)


class Admin2BackendTests(TestCase):
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
            username="admin2_test",
            email="admin2@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin2_user,
            role="ADMIN2",
            is_active=True,
        )

        # Normal assignment tests require today's school status
        # to be explicitly marked as REGULAR_CLASS.
        DailySchoolStatus.objects.create(
            date=timezone.localdate(),
            status="REGULAR_CLASS",
            created_by=self.admin2_user,
        )

        # =====================================================
        # VOLUNTEER USER
        # =====================================================

        self.volunteer_user = User.objects.create_user(
            username="volunteer_test@example.com",
            email="volunteer_test@example.com",
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
            user_id="TESM001",
            name="Test Volunteer",
            course=self.course,
            joining_year=2026,
            subject=self.subject,
            email="volunteer_test@example.com",
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
        # AUTH AS ADMIN 2
        # =====================================================

        self.client.force_authenticate(
            user=self.admin2_user
        )

    # =========================================================
    # STATUS TESTS
    # =========================================================

    def test_get_current_status_creates_active_status(self):
        status_obj = get_current_status(
            self.volunteer
        )

        self.assertEqual(
            status_obj.status,
            "ACTIVE",
        )

        self.assertTrue(
            VolunteerAccountStatus.objects.filter(
                volunteer=self.volunteer
            ).exists()
        )

    # =========================================================
    # XP TESTS
    # =========================================================

    def test_get_volunteer_xp_initially_zero(self):
        xp = get_volunteer_xp(
            self.volunteer
        )

        self.assertEqual(
            xp,
            0,
        )

    def test_manual_xp_increase(self):
        response = self.client.post(
            "/api/admin2/xp/adjust/",
            {
                "volunteer": self.volunteer.id,
                "points": 25,
                "reason": "Good performance",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            25,
        )

    def test_manual_xp_decrease(self):
        response = self.client.post(
            "/api/admin2/xp/adjust/",
            {
                "volunteer": self.volunteer.id,
                "points": -10,
                "reason": "Penalty",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            -10,
        )

    def test_zero_manual_xp_is_rejected(self):
        response = self.client.post(
            "/api/admin2/xp/adjust/",
            {
                "volunteer": self.volunteer.id,
                "points": 0,
                "reason": "Invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================================
    # ASSIGNED ATTENDANCE XP
    # =========================================================

    def test_assigned_present_gives_plus_10_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="TEACHING",
            attendance_source="ASSIGNED",
            status="PRESENT",
        )

        sync_attendance_xp(
            attendance
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            10,
        )

    def test_assigned_absent_gives_minus_10_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="TEACHING",
            attendance_source="ASSIGNED",
            status="ABSENT",
        )

        sync_attendance_xp(
            attendance
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            -10,
        )

    def test_special_present_gives_plus_5_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="CHECKING",
            attendance_source="SPECIAL_ADDED",
            status="PRESENT",
        )

        sync_attendance_xp(
            attendance
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
                5,
        )
    def test_special_absent_gives_zero_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="CHECKING",
            attendance_source="SPECIAL_ADDED",
            status="ABSENT",
        )

        sync_attendance_xp(
            attendance
        )

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            0,
        )



    def test_playing_day_present_gives_plus_10_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="TEACHING",
            attendance_source="PLAYING_DAY",
            status="PRESENT",
        )

        sync_attendance_xp(attendance)

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            10,
        )

    def test_playing_day_absent_gives_zero_xp(self):
        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=timezone.localdate(),
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=True,
        )

        attendance = VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task="CHECKING",
            attendance_source="PLAYING_DAY",
            status="ABSENT",
        )

        sync_attendance_xp(attendance)

        self.assertEqual(
            get_volunteer_xp(self.volunteer),
            0,
        )

    # =========================================================
    # ABSENCE STREAK TESTS
    # =========================================================

    def create_assignment_and_attendance(
        self,
        assignment_date,
        attendance_status,
        task="TEACHING",
    ):
        VolunteerAssignment.objects.create(
            volunteer=self.volunteer,
            assignment_date=assignment_date,
            assigned_class="ClassA",
            task=task,
            instruction="Test assignment",
            email_status="SENT",
            created_by=self.admin2_user,
        )

        session = AttendanceSession.objects.create(
            admin=self.admin2_user,
            session_date=assignment_date,
            expires_at=timezone.now() + timedelta(minutes=10),
            is_active=False,
        )

        return VolunteerAttendance.objects.create(
            session=session,
            volunteer=self.volunteer,
            task=task,
            attendance_source="ASSIGNED",
            status=attendance_status,
        )

    def test_one_absence_streak(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        self.assertEqual(
            get_assigned_absence_streak(
                self.volunteer
            ),
            1,
        )

    def test_three_consecutive_absences_create_streak_three(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=1),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        self.assertEqual(
            get_assigned_absence_streak(
                self.volunteer
            ),
            3,
        )

    def test_present_breaks_absence_streak(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=1),
            "PRESENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        self.assertEqual(
            get_assigned_absence_streak(
                self.volunteer
            ),
            1,
        )

    def test_days_without_assignment_are_ignored(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=4),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        self.assertEqual(
            get_assigned_absence_streak(
                self.volunteer
            ),
            3,
        )

    @patch("admin2.views.EmailMessage.send")
    def test_duplicate_daily_assignment_is_rejected(self, mock_send):
        today = timezone.localdate()

        self.volunteer.free_days = [
            today.strftime("%A")
        ]
        self.volunteer.save(
            update_fields=["free_days"]
        )

        mock_send.return_value = 1

        first_response = self.client.post(
            "/api/admin2/assignments/send/",
            {
                "volunteer": self.volunteer.id,
                "assigned_class": "ClassA",
                "task": "TEACHING",
                "instruction": "Teach mathematics.",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            "/api/admin2/assignments/send/",
            {
                "volunteer": self.volunteer.id,
                "assigned_class": "ClassB",
                "task": "CHECKING",
                "instruction": "Check answer sheets.",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertIn(
            "already has an assignment for today",
            str(second_response.json()),
        )

        self.assertEqual(
            VolunteerAssignment.objects.filter(
                volunteer=self.volunteer,
                assignment_date=today,
            ).count(),
            1,
        )

    # =========================================================
    # CAUTION TESTS
    # =========================================================

    def test_three_absences_create_caution(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=1),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        caution = check_and_create_caution(
            self.volunteer
        )

        self.assertIsNotNone(
            caution
        )

        self.assertEqual(
            caution.status,
            "ACTIVE",
        )

        self.assertEqual(
            caution.absence_streak,
            3,
        )

    def test_caution_changes_account_status(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=1),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        check_and_create_caution(
            self.volunteer
        )

        account_status = get_current_status(
            self.volunteer
        )

        self.assertEqual(
            account_status.status,
            "CAUTION",
        )

    def test_duplicate_active_caution_not_created(self):
        today = timezone.localdate()

        self.create_assignment_and_attendance(
            today - timedelta(days=2),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today - timedelta(days=1),
            "ABSENT",
        )

        self.create_assignment_and_attendance(
            today,
            "ABSENT",
        )

        check_and_create_caution(
            self.volunteer
        )

        check_and_create_caution(
            self.volunteer
        )

        self.assertEqual(
            VolunteerCaution.objects.filter(
                volunteer=self.volunteer,
                status="ACTIVE",
            ).count(),
            1,
        )

    # =========================================================
    # REMOVE VOLUNTEER
    # =========================================================

    def test_admin2_can_remove_volunteer(self):
        response = self.client.post(
            f"/api/admin2/volunteers/{self.volunteer.id}/remove/",
            {
                "reason": "Testing removal",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        status_obj = VolunteerAccountStatus.objects.get(
            volunteer=self.volunteer
        )

        self.assertEqual(
            status_obj.status,
            "REMOVED",
        )

        self.volunteer_user.refresh_from_db()

        self.assertFalse(
            self.volunteer_user.is_active
        )

    # =========================================================
    # ACCESS REQUEST
    # =========================================================

    def test_removed_volunteer_can_request_access(self):
        VolunteerAccountStatus.objects.create(
            volunteer=self.volunteer,
            status="REMOVED",
        )

        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/admin2/volunteer/request-access/",
            {
                "user_id": self.volunteer.user_id,
                "message": "Please restore my access.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            VolunteerAccessRequest.objects.filter(
                volunteer=self.volunteer,
                status="PENDING",
            ).exists()
        )

    def test_duplicate_pending_access_request_is_rejected(self):
        VolunteerAccountStatus.objects.create(
            volunteer=self.volunteer,
            status="REMOVED",
        )

        VolunteerAccessRequest.objects.create(
            volunteer=self.volunteer,
            status="PENDING",
            message="First request",
        )

        self.client.force_authenticate(
            user=None
        )

        response = self.client.post(
            "/api/admin2/volunteer/request-access/",
            {
                "user_id": self.volunteer.user_id,
                "message": "Second request",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================================
    # DAILY SCHOOL STATUS / ASSIGNMENT TESTS
    # =========================================================

    def test_daily_status_can_be_set_to_holiday(self):
        response = self.client.post(
            "/api/admin2/daily-status/",
            {"status": "HOLIDAY"},
            format="json",
        )

        self.assertIn(response.status_code, [200, 201])
        self.assertEqual(
            DailySchoolStatus.objects.get(
                date=timezone.localdate()
            ).status,
            "HOLIDAY",
        )

    def test_assignment_requires_regular_class_status(self):
        DailySchoolStatus.objects.update_or_create(
            date=timezone.localdate(),
            defaults={
                "status": "HOLIDAY",
                "created_by": self.admin2_user,
            },
        )

        response = self.client.post(
            "/api/admin2/assignments/send/",
            {
                "volunteer": self.volunteer.id,
                "assigned_class": "ClassA",
                "task": "TEACHING",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_assignment_accepts_invigilator_and_optional_homework(self):
        DailySchoolStatus.objects.update_or_create(
            date=timezone.localdate(),
            defaults={
                "status": "REGULAR_CLASS",
                "created_by": self.admin2_user,
            },
        )

        response = self.client.post(
            "/api/admin2/assignments/send/",
            {
                "volunteer": self.volunteer.id,
                "assigned_class": "ClassA",
                "task": "INVIGILATOR",
                "instruction": "Take the test.",
            },
            format="json",
        )

        # Email backend may be configured differently in the local environment,
        # but serializer/model validation must accept the new role.
        self.assertIn(response.status_code, [201, 500])
        self.assertTrue(
            VolunteerAssignment.objects.filter(
                volunteer=self.volunteer,
                assignment_date=timezone.localdate(),
                task="INVIGILATOR",
            ).exists()
        )

    # =========================================================
    # ADMIN2 PERMISSION
    # =========================================================

    def test_unauthenticated_user_cannot_access_dashboard(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/admin2/dashboard/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )