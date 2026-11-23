"""
Demo mode: one-click sign in for Volunteer, Admin 1 and Admin 2.

Disabled unless DEMO_MODE=true is set in the environment, so it can never
be switched on by accident in production. The demo accounts are ordinary
Django users with no usable password, so they cannot be used on the
normal sign-in forms.
"""

import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .serializers import UserProfileSerializer
from .utils import ensure_teacher_volunteer_profile

DEMO_ADMINS = {
    "ADMIN1": ("demo_admin1", "Demo", "Admin 1"),
    "ADMIN2": ("demo_admin2", "Demo", "Admin 2"),
}
DEMO_VOLUNTEER_EMAIL = "demo.volunteer@example.com"


def _demo_user(username, first_name, last_name, email=""):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        },
    )
    user.set_unusable_password()
    user.is_active = True
    user.save()
    return user


def _tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def _demo_volunteer():
    from courses.models import Course, Subject
    from teachers.models import Teacher
    from teachers.utils import generate_teacher_user_id

    user = _demo_user(
        "demo_volunteer", "Demo", "Volunteer", DEMO_VOLUNTEER_EMAIL
    )
    teacher = Teacher.objects.filter(email=DEMO_VOLUNTEER_EMAIL).first()
    if teacher is None:
        course, _ = Course.objects.get_or_create(name="Demo Course")
        subject, _ = Subject.objects.get_or_create(name="Demo Subject")
        teacher = Teacher(
            auth_user=user,
            user_id=generate_teacher_user_id("Demo Volunteer", subject),
            name="Demo Volunteer",
            course=course,
            subject=subject,
            joining_year=2025,
            email=DEMO_VOLUNTEER_EMAIL,
            whatsapp_number="0000000000",
            free_days=[],
            password=make_password(secrets.token_urlsafe(32)),
        )
        teacher.save()
    else:
        changed = []
        if teacher.auth_user_id != user.id:
            teacher.auth_user = user
            changed.append("auth_user")
        if not teacher.user_id:
            teacher.user_id = generate_teacher_user_id(
                teacher.name, teacher.subject
            )
            changed.append("user_id")
        if changed:
            teacher.save(update_fields=changed)
    return user, teacher


class DemoLoginView(APIView):
    """POST /api/auth/demo-login/  { "role": "ADMIN1" | "ADMIN2" | "VOLUNTEER" }"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not getattr(settings, "DEMO_MODE", False):
            return Response(
                {"detail": "Demo mode is not enabled."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = str(request.data.get("role", "")).upper()

        if role in DEMO_ADMINS:
            username, first, last = DEMO_ADMINS[role]
            user = _demo_user(username, first, last)
            profile, _ = UserProfile.objects.update_or_create(
                user=user, defaults={"role": role, "is_active": True}
            )
            return Response(
                {
                    "message": "Demo login successful.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                    },
                    "profile": UserProfileSerializer(profile).data,
                    "tokens": _tokens(user),
                }
            )

        if role == "VOLUNTEER":
            user, teacher = _demo_volunteer()
            profile = ensure_teacher_volunteer_profile(user)
            tokens = _tokens(user)
            return Response(
                {
                    "message": "Demo login successful.",
                    "user_id": teacher.user_id,
                    "name": teacher.name,
                    "email": teacher.email,
                    "course": teacher.course.name,
                    "subject": teacher.subject.name,
                    "role": profile.role,
                    "access": tokens["access"],
                    "refresh": tokens["refresh"],
                }
            )

        return Response(
            {"detail": "role must be ADMIN1, ADMIN2 or VOLUNTEER."},
            status=status.HTTP_400_BAD_REQUEST,
        )
