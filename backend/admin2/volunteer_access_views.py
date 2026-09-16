from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from teachers.models import Teacher

from .models import (
    VolunteerAccessRequest,
    VolunteerAccountStatus,
)
from .serializers import AccessRequestSerializer


class VolunteerRequestAccessView(APIView):
    permission_classes = [
        AllowAny
    ]

    def post(self, request):
        user_id = str(
            request.data.get(
                "user_id",
                ""
            )
        ).strip()

        message = str(
            request.data.get(
                "message",
                ""
            )
        ).strip()

        if not user_id:
            return Response(
                {
                    "detail":
                        "Volunteer ID is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        teacher = Teacher.objects.filter(
            user_id=user_id
        ).first()

        if not teacher:
            return Response(
                {
                    "detail":
                        "Volunteer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        account_status = (
            VolunteerAccountStatus.objects
            .filter(volunteer=teacher)
            .first()
        )

        if not account_status:
            return Response(
                {
                    "detail":
                        "Account status not configured."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if account_status.status != "REMOVED":
            return Response(
                {
                    "detail":
                        "This account does not require "
                        "Admin 2 permission."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = (
            VolunteerAccessRequest.objects
            .filter(
                volunteer=teacher,
                status="PENDING",
            )
            .first()
        )

        if existing:
            return Response(
                {
                    "detail":
                        "Access request already pending.",
                    "request":
                        AccessRequestSerializer(
                            existing
                        ).data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_request = (
            VolunteerAccessRequest.objects.create(
                volunteer=teacher,
                message=message,
            )
        )

        return Response(
            {
                "message":
                    "Access request submitted.",
                "request":
                    AccessRequestSerializer(
                        access_request
                    ).data,
            },
            status=status.HTTP_201_CREATED,
        )