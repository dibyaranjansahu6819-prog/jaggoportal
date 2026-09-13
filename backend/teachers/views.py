from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Teacher
from .serializers import TeacherRegistrationSerializer


class TeacherRegistrationView(generics.CreateAPIView):

    queryset = Teacher.objects.all()

    serializer_class = TeacherRegistrationSerializer


class TeacherLoginView(APIView):

    def post(self, request):

        user_id = request.data.get("user_id", "").strip()
        password = request.data.get("password", "")

        if not user_id:
            return Response(
                {
                    "error": "Teacher User ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password:
            return Response(
                {
                    "error": "Password is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            teacher = Teacher.objects.get(
                user_id=user_id
            )
        except Teacher.DoesNotExist:

            return Response(
                {
                    "error": "Invalid Teacher User ID or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Existing teacher created before Django User
        # authentication was added.
        if teacher.auth_user is None:

            from django.contrib.auth.models import User

            # Verify the password stored in Teacher
            from django.contrib.auth.hashers import check_password

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

            # Create authentication account for the
            # existing teacher.
            auth_user = User.objects.create_user(
                username=teacher.email,
                email=teacher.email,
                password=password,
                first_name=teacher.name,
            )

            teacher.auth_user = auth_user
            teacher.save(
                update_fields=["auth_user"]
            )

        else:

            auth_user = teacher.auth_user

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

        refresh = RefreshToken.for_user(
            auth_user
        )

        return Response(
            {
                "message": "Login successful.",
                "user_id": teacher.user_id,
                "name": teacher.name,
                "email": teacher.email,
                "course": teacher.course.name,
                "subject": teacher.subject.name,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )