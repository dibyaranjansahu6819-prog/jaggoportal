from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from accounts.utils import ensure_teacher_volunteer_profile
from admin2.models import VolunteerAccountStatus

from .models import Teacher
from .serializers import TeacherRegistrationSerializer


# ============================================================
# VOLUNTEER REGISTRATION
# ============================================================

class TeacherRegistrationView(generics.CreateAPIView):

    queryset = Teacher.objects.all()

    serializer_class = TeacherRegistrationSerializer

    # Volunteer registration is public.
    permission_classes = [
        AllowAny
    ]


# ============================================================
# VOLUNTEER LOGIN
# ============================================================

class TeacherLoginView(APIView):

    # Login is public because the volunteer does not
    # have a JWT before logging in.
    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        # ----------------------------------------------------
        # GET LOGIN DATA
        # ----------------------------------------------------

        user_id = request.data.get(
            "user_id",
            ""
        )

        password = request.data.get(
            "password",
            ""
        )

        if not isinstance(user_id, str):
            user_id = str(user_id)

        user_id = user_id.strip()

        if not user_id:

            return Response(
                {
                    "error":
                        "Teacher User ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password:

            return Response(
                {
                    "error":
                        "Password is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # FIND VOLUNTEER
        # ----------------------------------------------------

        try:

            teacher = Teacher.objects.select_related(
                "auth_user",
                "course",
                "subject",
            ).get(
                user_id=user_id
            )

        except Teacher.DoesNotExist:

            return Response(
                {
                    "error":
                        "Invalid Teacher User ID or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ----------------------------------------------------
        # CHECK ADMIN 2 ACCOUNT STATUS
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # If Admin 2 has removed this volunteer, do not
        # allow normal login.
        #
        # Instead return a special code that the frontend
        # can use to display:
        #
        # "Your account has been removed."
        #
        # "Request Access"
        #
        # The volunteer can then use the public
        # request-access endpoint.
        #
        # ----------------------------------------------------

        account_status = (
            VolunteerAccountStatus.objects
            .filter(
                volunteer=teacher
            )
            .first()
        )

        if (
            account_status
            and account_status.status == "REMOVED"
        ):

            return Response(
                {
                    "error": (
                        "Your volunteer account has "
                        "been removed by Admin 2."
                    ),

                    "code":
                        "VOLUNTEER_REMOVED",

                    "access_request_allowed":
                        True,

                    "message": (
                        "You must request permission "
                        "from Admin 2 before you can "
                        "access your volunteer dashboard."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------------------------------
        # EXISTING LEGACY VOLUNTEER
        # ----------------------------------------------------
        #
        # This supports volunteers that were created before
        # the Django User authentication account was linked.
        #
        # ----------------------------------------------------

        if teacher.auth_user is None:

            from django.contrib.auth.hashers import (
                check_password
            )

            if not check_password(
                password,
                teacher.password
            ):

                return Response(
                    {
                        "error":
                            "Invalid Teacher User ID or password."
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # ------------------------------------------------
            # CREATE DJANGO AUTH USER
            # ------------------------------------------------

            try:

                auth_user = User.objects.create_user(
                    username=teacher.email,
                    email=teacher.email,
                    password=password,
                    first_name=teacher.name,
                )

            except Exception:

                return Response(
                    {
                        "error": (
                            "Unable to create the "
                            "authentication account."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            teacher.auth_user = auth_user

            teacher.save(
                update_fields=[
                    "auth_user"
                ]
            )

        # ----------------------------------------------------
        # NORMAL VOLUNTEER LOGIN
        # ----------------------------------------------------

        else:

            auth_user = teacher.auth_user

            # ------------------------------------------------
            # CHECK DJANGO USER STATUS
            # ------------------------------------------------

            if not auth_user.is_active:

                return Response(
                    {
                        "error":
                            "This teacher account is inactive."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # ------------------------------------------------
            # CHECK PASSWORD
            # ------------------------------------------------

            authenticated_user = authenticate(
                username=auth_user.username,
                password=password
            )

            if authenticated_user is None:

                return Response(
                    {
                        "error":
                            "Invalid Teacher User ID or password."
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Use the authenticated user object.
            auth_user = authenticated_user

        # ----------------------------------------------------
        # ENSURE VOLUNTEER ROLE
        # ----------------------------------------------------
        #
        # Teacher and Volunteer are one role in Jaago Portal:
        #
        # TEACHER_VOLUNTEER
        #
        # ----------------------------------------------------

        profile = ensure_teacher_volunteer_profile(
            auth_user
        )

        # ----------------------------------------------------
        # GENERATE JWT
        # ----------------------------------------------------

        refresh = RefreshToken.for_user(
            auth_user
        )

        access_token = refresh.access_token

        # ----------------------------------------------------
        # LOGIN SUCCESS RESPONSE
        # ----------------------------------------------------

        return Response(
            {
                "message":
                    "Login successful.",

                "user_id":
                    teacher.user_id,

                "name":
                    teacher.name,

                "email":
                    teacher.email,

                "course":
                    teacher.course.name,

                "subject":
                    teacher.subject.name,

                "role":
                    profile.role,

                "access":
                    str(
                        access_token
                    ),

                "refresh":
                    str(
                        refresh
                    ),
            },
            status=status.HTTP_200_OK
        )