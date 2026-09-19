from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsTeacherVolunteer
from attendance.models import VolunteerAttendance
from admin2.models import VolunteerAccountStatus, VolunteerAssignment

from .models import SpecialAddedWorkAccess, Teacher


SPECIAL_ADDED_SOURCE = "SPECIAL_ADDED"
ASSIGNED_SOURCE = "ASSIGNED"


def get_current_volunteer(request):
    return (
        Teacher.objects
        .select_related("subject", "course")
        .filter(auth_user=request.user)
        .first()
    )


def get_account_status(volunteer):
    account_status = (
        VolunteerAccountStatus.objects
        .filter(volunteer=volunteer)
        .first()
    )

    if account_status is None:
        return "ACTIVE"

    return account_status.status


def removed_response():
    return Response(
        {
            "error": (
                "Your volunteer account has been removed "
                "by Admin 2."
            ),
            "code": "VOLUNTEER_REMOVED",
            "access_request_allowed": True,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def get_today_attendance_for_volunteer(volunteer):
    today = timezone.localdate()

    return (
        VolunteerAttendance.objects
        .filter(
            session__session_date=today,
            volunteer=volunteer,
        )
        .select_related("session")
        .order_by("-session__started_at", "-marked_at")
        .first()
    )


def get_special_added_present_attendance(volunteer):
    attendance = get_today_attendance_for_volunteer(volunteer)

    if (
        attendance is None
        or attendance.attendance_source != SPECIAL_ADDED_SOURCE
        or attendance.status != "PRESENT"
    ):
        return None

    return attendance


def get_today_absent_assigned_assignments():
    """
    Return today's SENT assignments whose original volunteer
    was marked ABSENT in today's Admin1 attendance.

    A work assignment already selected by another Special Added
    volunteer is not available again.
    """

    today = timezone.localdate()

    assignments = (
        VolunteerAssignment.objects
        .filter(
            assignment_date=today,
            email_status="SENT",
        )
        .select_related(
            "volunteer",
            "volunteer__subject",
        )
        .order_by(
            "volunteer__name",
            "id",
        )
    )

    available = []

    for assignment in assignments:
        attendance = (
            VolunteerAttendance.objects
            .filter(
                session__session_date=today,
                volunteer=assignment.volunteer,
                attendance_source=ASSIGNED_SOURCE,
            )
            .order_by(
                "-session__started_at",
                "-marked_at",
            )
            .first()
        )

        if attendance is None:
            continue

        if attendance.status != "ABSENT":
            continue

        if SpecialAddedWorkAccess.objects.filter(
            assignment=assignment
        ).exists():
            continue

        available.append(
            {
                "assignment": assignment,
                "attendance": attendance,
            }
        )

    return available


def serialize_assignment(assignment):
    return {
        "id": assignment.id,
        "date": assignment.assignment_date,
        "original_volunteer": {
            "id": assignment.volunteer.id,
            "user_id": assignment.volunteer.user_id,
            "name": assignment.volunteer.name,
        },
        "class": assignment.assigned_class,
        "task": assignment.task,
        "instruction": assignment.instruction,
        "attachment": (
            assignment.attachment.url
            if assignment.attachment
            else None
        ),
        "homework_attachment": (
            assignment.homework_attachment.url
            if assignment.homework_attachment
            else None
        ),
        "email_status": assignment.email_status,
    }


class SpecialAddedAvailableWorkView(APIView):
    """
    GET today's work that a Special Added + PRESENT volunteer
    may choose.

    Only assignments of volunteers marked ABSENT are returned.
    """

    permission_classes = [
        IsAuthenticated,
        IsTeacherVolunteer,
    ]

    def get(self, request):
        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_account_status(volunteer) == "REMOVED":
            return removed_response()

        attendance = get_special_added_present_attendance(
            volunteer
        )

        if attendance is None:
            return Response(
                {
                    "eligible": False,
                    "available_work": [],
                    "message": (
                        "Special Added work is available only "
                        "after you are added by Admin 1 and "
                        "marked PRESENT."
                    ),
                }
            )

        existing_access = (
            SpecialAddedWorkAccess.objects
            .filter(
                special_volunteer=volunteer,
                access_date=timezone.localdate(),
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
            )
            .first()
        )

        if existing_access:
            return Response(
                {
                    "eligible": True,
                    "selected": True,
                    "work": serialize_assignment(
                        existing_access.assignment
                    ),
                    "access_id": existing_access.id,
                    "access_status": existing_access.status,
                    "message": (
                        "You have already selected today's work."
                    ),
                }
            )

        available = get_today_absent_assigned_assignments()

        return Response(
            {
                "eligible": True,
                "selected": False,
                "available_work": [
                    serialize_assignment(item["assignment"])
                    for item in available
                ],
                "message": (
                    "Choose one available absent-volunteer "
                    "assignment."
                    if available
                    else (
                        "No absent assigned volunteer work "
                        "is currently available."
                    )
                ),
            }
        )


class SpecialAddedSelectWorkView(APIView):
    """
    POST:
        {"assignment": <assignment_id>}

    The authenticated volunteer must:
      1. be active;
      2. be Special Added + PRESENT today;
      3. not already have selected work today;
      4. select an assignment whose original volunteer is
         marked ABSENT today;
      5. select an assignment not already taken.
    """

    permission_classes = [
        IsAuthenticated,
        IsTeacherVolunteer,
    ]

    @transaction.atomic
    def post(self, request):
        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_account_status(volunteer) == "REMOVED":
            return removed_response()

        attendance = get_special_added_present_attendance(
            volunteer
        )

        if attendance is None:
            return Response(
                {
                    "error": (
                        "You must be added by Admin 1 and "
                        "marked PRESENT before selecting work."
                    ),
                    "code": "SPECIAL_ADDED_NOT_PRESENT",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        existing_access = (
            SpecialAddedWorkAccess.objects
            .filter(
                special_volunteer=volunteer,
                access_date=timezone.localdate(),
            )
            .first()
        )

        if existing_access:
            return Response(
                {
                    "error": (
                        "You have already selected one "
                        "work assignment today."
                    ),
                    "code": "WORK_ALREADY_SELECTED",
                    "access_id": existing_access.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignment_id = request.data.get("assignment")

        if not assignment_id:
            return Response(
                {
                    "error": "assignment is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assignment = (
                VolunteerAssignment.objects
                .select_related(
                    "volunteer",
                    "volunteer__subject",
                )
                .get(
                    id=assignment_id,
                    assignment_date=timezone.localdate(),
                    email_status="SENT",
                )
            )
        except VolunteerAssignment.DoesNotExist:
            return Response(
                {
                    "error": (
                        "The requested assignment is not "
                        "available today."
                    ),
                    "code": "ASSIGNMENT_NOT_AVAILABLE",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if assignment.volunteer_id == volunteer.id:
            return Response(
                {
                    "error": (
                        "You cannot select your own assignment "
                        "as Special Added work."
                    ),
                    "code": "OWN_ASSIGNMENT_NOT_ALLOWED",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_attendance = (
            VolunteerAttendance.objects
            .filter(
                session__session_date=timezone.localdate(),
                volunteer=assignment.volunteer,
                attendance_source=ASSIGNED_SOURCE,
            )
            .order_by(
                "-session__started_at",
                "-marked_at",
            )
            .first()
        )

        if original_attendance is None:
            return Response(
                {
                    "error": (
                        "The original volunteer has no "
                        "assigned attendance record yet."
                    ),
                    "code": "ORIGINAL_ATTENDANCE_MISSING",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if original_attendance.status != "ABSENT":
            return Response(
                {
                    "error": (
                        "Only work belonging to an absent "
                        "assigned volunteer can be selected."
                    ),
                    "code": "ORIGINAL_VOLUNTEER_NOT_ABSENT",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if SpecialAddedWorkAccess.objects.filter(
            assignment=assignment
        ).exists():
            return Response(
                {
                    "error": (
                        "This work has already been selected "
                        "by another Special Added volunteer."
                    ),
                    "code": "WORK_ALREADY_TAKEN",
                },
                status=status.HTTP_409_CONFLICT,
            )

        access = SpecialAddedWorkAccess.objects.create(
            special_volunteer=volunteer,
            assignment=assignment,
            attendance=attendance,
            access_date=timezone.localdate(),
            status="ACTIVE",
        )

        return Response(
            {
                "message": (
                    "Work selected successfully."
                ),
                "access_id": access.id,
                "status": access.status,
                "work": serialize_assignment(
                    assignment
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class SpecialAddedCurrentWorkView(APIView):
    """
    GET the work already selected by the current Special Added
    volunteer today.
    """

    permission_classes = [
        IsAuthenticated,
        IsTeacherVolunteer,
    ]

    def get(self, request):
        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_account_status(volunteer) == "REMOVED":
            return removed_response()

        attendance = get_special_added_present_attendance(
            volunteer
        )

        if attendance is None:
            return Response(
                {
                    "eligible": False,
                    "work": None,
                }
            )

        access = (
            SpecialAddedWorkAccess.objects
            .filter(
                special_volunteer=volunteer,
                access_date=timezone.localdate(),
            )
            .select_related(
                "assignment",
                "assignment__volunteer",
                "assignment__volunteer__subject",
            )
            .first()
        )

        if access is None:
            return Response(
                {
                    "eligible": True,
                    "selected": False,
                    "work": None,
                }
            )

        return Response(
            {
                "eligible": True,
                "selected": True,
                "access_id": access.id,
                "status": access.status,
                "work": serialize_assignment(
                    access.assignment
                ),
            }
        )
