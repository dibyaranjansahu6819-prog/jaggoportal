from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from courses.models import Course, Subject

from .models import Teacher


class TeacherRegistrationTests(APITestCase):

    def setUp(self):
        self.course = Course.objects.create(
            name="Science"
        )

        self.subject = Subject.objects.create(
            name="Mathematics"
        )

    def test_teacher_registration_success(self):

        response = self.client.post(
            "/api/teachers/register/",
            {
                "name": "Dibyaranjan Sahu",
                "course": self.course.id,
                "joining_year": 2026,
                "subject": self.subject.id,
                "email": "dibya@example.com",
                "whatsapp_number": "9876543210",
                "free_days": [
                    "Monday",
                    "Wednesday",
                ],
                "password": "TestPassword123",
                "confirm_password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # Teacher was created
        self.assertEqual(
            Teacher.objects.count(),
            1
        )

        teacher = Teacher.objects.first()

        self.assertEqual(
            teacher.name,
            "Dibyaranjan Sahu"
        )

        # Generated Teacher ID exists
        self.assertTrue(
            teacher.user_id
        )

        # Django authentication user exists
        self.assertIsNotNone(
            teacher.auth_user
        )

        self.assertEqual(
            teacher.auth_user.email,
            "dibya@example.com"
        )

        # Teacher gets the unified Teacher/Volunteer role
        profile = UserProfile.objects.get(
            user=teacher.auth_user
        )

        self.assertEqual(
            profile.role,
            "TEACHER_VOLUNTEER"
        )

    def test_teacher_registration_password_mismatch(self):

        response = self.client.post(
            "/api/teachers/register/",
            {
                "name": "Rahul Das",
                "course": self.course.id,
                "joining_year": 2026,
                "subject": self.subject.id,
                "email": "rahul@example.com",
                "whatsapp_number": "9876543211",
                "free_days": [
                    "Tuesday",
                ],
                "password": "TestPassword123",
                "confirm_password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            Teacher.objects.count(),
            0
        )

    def test_teacher_registration_rejects_sunday(self):

        response = self.client.post(
            "/api/teachers/register/",
            {
                "name": "Ankit Patra",
                "course": self.course.id,
                "joining_year": 2026,
                "subject": self.subject.id,
                "email": "ankit@example.com",
                "whatsapp_number": "9876543212",
                "free_days": [
                    "Sunday",
                ],
                "password": "TestPassword123",
                "confirm_password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            Teacher.objects.count(),
            0
        )

    def test_teacher_registration_requires_free_day(self):

        response = self.client.post(
            "/api/teachers/register/",
            {
                "name": "Sourav Das",
                "course": self.course.id,
                "joining_year": 2026,
                "subject": self.subject.id,
                "email": "sourav@example.com",
                "whatsapp_number": "9876543213",
                "free_days": [],
                "password": "TestPassword123",
                "confirm_password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )


class TeacherLoginTests(APITestCase):

    def setUp(self):

        self.course = Course.objects.create(
            name="Science"
        )

        self.subject = Subject.objects.create(
            name="Mathematics"
        )

        response = self.client.post(
            "/api/teachers/register/",
            {
                "name": "Dibyaranjan Sahu",
                "course": self.course.id,
                "joining_year": 2026,
                "subject": self.subject.id,
                "email": "dibya@example.com",
                "whatsapp_number": "9876543210",
                "free_days": [
                    "Monday",
                    "Friday",
                ],
                "password": "TestPassword123",
                "confirm_password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.teacher = Teacher.objects.get(
            email="dibya@example.com"
        )

    def test_teacher_login_success(self):

        response = self.client.post(
            "/api/teachers/login/",
            {
                "user_id": self.teacher.user_id,
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            "access",
            response.data
        )

        self.assertIn(
            "refresh",
            response.data
        )

        self.assertEqual(
            response.data["user_id"],
            self.teacher.user_id
        )

        self.assertEqual(
            response.data["role"],
            "TEACHER_VOLUNTEER"
        )

    def test_teacher_login_wrong_password(self):

        response = self.client.post(
            "/api/teachers/login/",
            {
                "user_id": self.teacher.user_id,
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_teacher_login_wrong_user_id(self):

        response = self.client.post(
            "/api/teachers/login/",
            {
                "user_id": "INVALID001",
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class TeacherRoleTests(APITestCase):

    def test_teacher_volunteer_role_value(self):

        user = User.objects.create_user(
            username="teacher@example.com",
            email="teacher@example.com",
            password="TestPassword123",
        )

        profile = UserProfile.objects.create(
            user=user,
            role="TEACHER_VOLUNTEER",
        )

        self.assertEqual(
            profile.role,
            "TEACHER_VOLUNTEER"
        )