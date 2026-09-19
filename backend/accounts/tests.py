from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import UserProfile


class AccountsModelTests(APITestCase):

    def test_user_profile_creation(self):
        user = User.objects.create_user(
            username="testadmin",
            password="TestPassword123"
        )

        profile = UserProfile.objects.create(
            user=user,
            role="ADMIN1"
        )

        self.assertEqual(profile.role, "ADMIN1")
        self.assertEqual(profile.user.username, "testadmin")


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin1",
            password="TestPassword123"
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            role="ADMIN1"
        )

    def test_login_success(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "admin1",
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "tokens",
            response.data
        )

        self.assertIn(
            "access",
            response.data["tokens"]
        )

        self.assertIn(
            "refresh",
            response.data["tokens"]
        )

        self.assertEqual(
            response.data["profile"]["role"],
            "ADMIN1"
        )

    def test_login_wrong_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "admin1",
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_current_user_requires_authentication(self):
        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_current_user_with_jwt(self):
        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "admin1",
                "password": "TestPassword123",
            },
            format="json",
        )

        access_token = login_response.data["tokens"]["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["profile"]["role"],
            "ADMIN1"
        )


class PermissionTests(APITestCase):

    def setUp(self):
        self.admin1 = User.objects.create_user(
            username="admin1",
            password="TestPassword123"
        )

        UserProfile.objects.create(
            user=self.admin1,
            role="ADMIN1"
        )

        self.admin2 = User.objects.create_user(
            username="admin2",
            password="TestPassword123"
        )

        UserProfile.objects.create(
            user=self.admin2,
            role="ADMIN2"
        )

        self.teacher = User.objects.create_user(
            username="teacher1",
            password="TestPassword123"
        )

        UserProfile.objects.create(
            user=self.teacher,
            role="TEACHER_VOLUNTEER"
        )

        self.student = User.objects.create_user(
            username="student1",
            password="TestPassword123"
        )

        UserProfile.objects.create(
            user=self.student,
            role="STUDENT"
        )

    def test_all_roles_exist(self):
        roles = UserProfile.objects.values_list(
            "role",
            flat=True
        )

        self.assertIn("ADMIN1", roles)
        self.assertIn("ADMIN2", roles)
        self.assertIn("TEACHER_VOLUNTEER", roles)
        self.assertIn("STUDENT", roles)

class PasswordResetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="resetadmin",
            email="reset@example.com",
            password="OldPassword123!",
            first_name="Reset",
            last_name="Admin",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            role="ADMIN1",
        )

    def test_forgot_password_sends_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {"email": "reset@example.com"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            ["reset@example.com"],
        )
        self.assertIn("Password Reset", mail.outbox[0].subject)

    def test_forgot_password_does_not_reveal_unknown_email(self):
        response = self.client.post(
            "/api/auth/forgot-password/",
            {"email": "unknown@example.com"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn(
            "If an account exists",
            response.data["message"],
        )

    def test_reset_password_changes_password(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uidb64 = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )
        token = default_token_generator.make_token(
            self.user
        )

        response = self.client.post(
            f"/api/auth/reset-password/{uidb64}/{token}/",
            {
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword123!")
        )
        self.assertFalse(
            self.user.check_password("OldPassword123!")
        )

    def test_reset_password_token_cannot_be_reused(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uidb64 = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )
        token = default_token_generator.make_token(
            self.user
        )

        first_response = self.client.post(
            f"/api/auth/reset-password/{uidb64}/{token}/",
            {
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            f"/api/auth/reset-password/{uidb64}/{token}/",
            {
                "new_password": "AnotherPassword123!",
                "confirm_password": "AnotherPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reset_password_rejects_mismatched_passwords(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uidb64 = urlsafe_base64_encode(
            force_bytes(self.user.pk)
        )
        token = default_token_generator.make_token(
            self.user
        )

        response = self.client.post(
            f"/api/auth/reset-password/{uidb64}/{token}/",
            {
                "new_password": "NewPassword123!",
                "confirm_password": "DifferentPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertTrue(
            self.user.check_password("OldPassword123!")
        )
