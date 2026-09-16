from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserProfileSerializer
from .utils import get_user_profile


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a user.
    """

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class LoginView(APIView):
    """
    Common login endpoint.

    Used by:
        - Admin 1
        - Admin 2
        - Teacher / Volunteer

    Students do not use this endpoint in the current system.
    """

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(
            username=username,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "detail": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {
                    "detail": "This account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = get_user_profile(user)

        if profile is None:
            return Response(
                {
                    "detail": "User profile is not configured."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = get_tokens_for_user(user)

        return Response(
            {
                "message": "Login successful.",

                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                },

                "profile": UserProfileSerializer(
                    profile
                ).data,

                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    Return information about the currently
    authenticated user.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        profile = get_user_profile(
            request.user
        )

        if profile is None:
            return Response(
                {
                    "detail": "User profile is not configured."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "email": request.user.email,
                },

                "profile": UserProfileSerializer(
                    profile
                ).data,
            },
            status=status.HTTP_200_OK,
        )