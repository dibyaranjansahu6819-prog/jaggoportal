from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from rest_framework.test import APIClient

from accounts.models import UserProfile
from attendance.models import Holiday


class HolidayBackendTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.admin2_user = User.objects.create_user(
            username="holiday_admin2",
            email="holiday_admin2@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=self.admin2_user,
            role="ADMIN2",
            is_active=True,
        )

        self.client.force_authenticate(
            user=self.admin2_user,
        )

    # =========================================================
    # CREATE
    # =========================================================

    def test_admin2_can_create_holiday(self):
        holiday_date = timezone.localdate() + timedelta(
            days=10,
        )

        response = self.client.post(
            "/api/admin2/holidays/",
            {
                "date": holiday_date.isoformat(),
                "name": "Independence Day",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            Holiday.objects.filter(
                date=holiday_date,
                name="Independence Day",
                is_active=True,
            ).exists()
        )

    # =========================================================
    # LIST
    # =========================================================

    def test_admin2_can_list_holidays(self):
        holiday_date = timezone.localdate() + timedelta(
            days=5,
        )

        Holiday.objects.create(
            date=holiday_date,
            name="Test Holiday",
            created_by=self.admin2_user,
        )

        response = self.client.get(
            "/api/admin2/holidays/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn(
            "count",
            data,
        )

        self.assertIn(
            "holidays",
            data,
        )

        self.assertEqual(
            len(data["holidays"]),
            1,
        )

    # =========================================================
    # DUPLICATE DATE
    # =========================================================

    def test_duplicate_holiday_date_is_rejected(self):
        holiday_date = timezone.localdate() + timedelta(
            days=7,
        )

        Holiday.objects.create(
            date=holiday_date,
            name="First Holiday",
            created_by=self.admin2_user,
        )

        response = self.client.post(
            "/api/admin2/holidays/",
            {
                "date": holiday_date.isoformat(),
                "name": "Second Holiday",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # =========================================================
    # DEACTIVATE
    # =========================================================

    def test_admin2_can_deactivate_holiday(self):
        holiday_date = timezone.localdate() + timedelta(
            days=8,
        )

        holiday = Holiday.objects.create(
            date=holiday_date,
            name="Test Holiday",
            created_by=self.admin2_user,
        )

        response = self.client.patch(
            f"/api/admin2/holidays/{holiday.id}/",
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        holiday.refresh_from_db()

        self.assertFalse(
            holiday.is_active,
        )

    # =========================================================
    # REACTIVATE
    # =========================================================

    def test_admin2_can_reactivate_holiday(self):
        holiday_date = timezone.localdate() + timedelta(
            days=9,
        )

        holiday = Holiday.objects.create(
            date=holiday_date,
            name="Test Holiday",
            created_by=self.admin2_user,
            is_active=False,
        )

        response = self.client.patch(
            f"/api/admin2/holidays/{holiday.id}/",
            {
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        holiday.refresh_from_db()

        self.assertTrue(
            holiday.is_active,
        )

    # =========================================================
    # UPDATE NAME
    # =========================================================

    def test_admin2_can_update_holiday_name(self):
        holiday_date = timezone.localdate() + timedelta(
            days=11,
        )

        holiday = Holiday.objects.create(
            date=holiday_date,
            name="Old Name",
            created_by=self.admin2_user,
        )

        response = self.client.patch(
            f"/api/admin2/holidays/{holiday.id}/",
            {
                "name": "Updated Holiday Name",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        holiday.refresh_from_db()

        self.assertEqual(
            holiday.name,
            "Updated Holiday Name",
        )

    # =========================================================
    # HOLIDAY MODEL HELPER
    # =========================================================

    def test_is_holiday_returns_true_for_active_holiday(self):
        holiday_date = timezone.localdate() + timedelta(
            days=12,
        )

        Holiday.objects.create(
            date=holiday_date,
            name="School Holiday",
            created_by=self.admin2_user,
        )

        self.assertTrue(
            Holiday.is_holiday(
                holiday_date,
            )
        )

    def test_is_holiday_returns_false_for_inactive_holiday(self):
        holiday_date = timezone.localdate() + timedelta(
            days=13,
        )

        Holiday.objects.create(
            date=holiday_date,
            name="Inactive Holiday",
            created_by=self.admin2_user,
            is_active=False,
        )

        self.assertFalse(
            Holiday.is_holiday(
                holiday_date,
            )
        )

    # =========================================================
    # PERMISSION
    # =========================================================

    def test_unauthenticated_user_cannot_list_holidays(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            "/api/admin2/holidays/",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_admin2_permission_is_required(self):
        admin1_user = User.objects.create_user(
            username="holiday_admin1",
            email="holiday_admin1@example.com",
            password="AdminPassword123",
        )

        UserProfile.objects.create(
            user=admin1_user,
            role="ADMIN1",
            is_active=True,
        )

        self.client.force_authenticate(
            user=admin1_user,
        )

        response = self.client.get(
            "/api/admin2/holidays/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )