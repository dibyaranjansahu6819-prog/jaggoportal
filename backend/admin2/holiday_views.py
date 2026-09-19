from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin2
from attendance.models import Holiday

from .holiday_serializers import HolidaySerializer


class Admin2HolidayBaseView(APIView):
    """
    Base permission for Holiday management.

    Only authenticated Admin2 users can access the holiday APIs.
    """

    permission_classes = [
        IsAdmin2,
    ]


class HolidayListCreateView(Admin2HolidayBaseView):
    """
    GET:
        Return all holidays.

    POST:
        Create a new holiday.
    """

    def get(self, request):
        holidays = Holiday.objects.all().select_related(
            "created_by",
        )

        serializer = HolidaySerializer(
            holidays,
            many=True,
        )

        return Response(
            {
                "count": holidays.count(),
                "holidays": serializer.data,
            }
        )

    def post(self, request):
        serializer = HolidaySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        holiday = serializer.save(
            created_by=request.user,
        )

        return Response(
            {
                "message": "Holiday created successfully.",
                "holiday": HolidaySerializer(
                    holiday,
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class HolidayDetailView(Admin2HolidayBaseView):
    """
    PATCH:
        Update a holiday.

    Currently this is intended mainly for:
        - changing holiday name
        - activating a holiday
        - deactivating a holiday

    DELETE is intentionally not provided.

    Historical holiday records should be preserved rather than
    physically deleted.
    """

    def patch(self, request, holiday_id):
        holiday = get_object_or_404(
            Holiday,
            id=holiday_id,
        )

        serializer = HolidaySerializer(
            holiday,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        holiday = serializer.save()

        return Response(
            {
                "message": "Holiday updated successfully.",
                "holiday": HolidaySerializer(
                    holiday,
                ).data,
            }
        )