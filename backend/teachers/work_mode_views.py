from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsTeacherVolunteer
from admin2.models import VolunteerAssignment, VolunteerAccountStatus
from .models import Teacher, VolunteerWorkSession, SpecialAddedWorkAccess


def get_current_volunteer(request):
    try:
        return Teacher.objects.select_related(
            "subject",
            "course",
        ).get(
            auth_user=request.user
        )
    except Teacher.DoesNotExist:
        return None


def get_volunteer_account_status(volunteer):
    account_status = (
        VolunteerAccountStatus.objects
        .filter(volunteer=volunteer)
        .first()
    )

    if account_status is None:
        return "ACTIVE"

    return account_status.status


def get_today_own_assignment(volunteer):
    today = timezone.localdate()

    return (
        VolunteerAssignment.objects
        .filter(
            volunteer=volunteer,
            assignment_date=today,
            email_status="SENT",
        )
        .first()
    )


def get_today_special_added_access(volunteer):
    today = timezone.localdate()

    return (
        SpecialAddedWorkAccess.objects
        .select_related(
            "assignment",
            "attendance",
        )
        .filter(
            special_volunteer=volunteer,
            access_date=today,
            status__in=["ACTIVE", "COMPLETED"],
            assignment__assignment_date=today,
            assignment__email_status="SENT",
            attendance__volunteer=volunteer,
            attendance__attendance_source="SPECIAL_ADDED",
            attendance__status="PRESENT",
        )
        .first()
    )


class VolunteerWorkModeView(APIView):
    """
    Return the current work mode for the logged-in volunteer.

    Possible modes:

        TEACHING
        CHECKING
        INVIGILATOR

    Special Added work is also supported. In that case the
    selected assignment is returned while preserving the
    original assignment owner.
    """

    permission_classes = [
        IsTeacherVolunteer,
    ]

    def get(self, request):

        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_volunteer_account_status(volunteer) == "REMOVED":
            return Response(
                {
                    "error": (
                        "Your volunteer account has been "
                        "removed by Admin 2."
                    ),
                    "code": "VOLUNTEER_REMOVED",
                    "access_request_allowed": True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        today = timezone.localdate()

        # --------------------------------------------------------
        # SPECIAL ADDED WORK HAS PRIORITY
        # --------------------------------------------------------

        special_access = get_today_special_added_access(
            volunteer
        )

        if special_access is not None:
            assignment = special_access.assignment
            work_source = "SPECIAL_ADDED"

        else:
            assignment = get_today_own_assignment(
                volunteer
            )
            work_source = "ASSIGNED"

        # --------------------------------------------------------
        # NO WORK
        # --------------------------------------------------------

        if assignment is None:
            return Response(
                {
                    "date": today,
                    "work_mode": None,
                    "work_source": "NONE",
                    "assignment": None,
                    "work_session": None,
                    "message": "No work assigned for today.",
                },
                status=status.HTTP_200_OK,
            )

        # --------------------------------------------------------
        # GET ACTUAL VOLUNTEER'S SESSION
        # --------------------------------------------------------

        work_session = (
            VolunteerWorkSession.objects
            .filter(
                assignment=assignment,
                volunteer=volunteer,
            )
            .first()
        )

        # --------------------------------------------------------
        # WORK MODE
        # --------------------------------------------------------

        task_display = dict(
            VolunteerAssignment.TASK_CHOICES
        ).get(
            assignment.task,
            assignment.task,
        )

        # --------------------------------------------------------
        # SESSION DATA
        # --------------------------------------------------------

        session_data = None

        if work_session is not None:

            elapsed_seconds = 0

            if (
                work_session.status == "COMPLETED"
                and work_session.total_seconds is not None
            ):
                elapsed_seconds = (
                    work_session.total_seconds
                )

            elif (
                work_session.status == "IN_PROGRESS"
                and work_session.started_at
            ):
                elapsed_seconds = max(
                    0,
                    int(
                        (
                            timezone.now()
                            - work_session.started_at
                        ).total_seconds()
                    ),
                )

            session_data = {
                "id": work_session.id,
                "status": work_session.status,
                "started_at": work_session.started_at,
                "ended_at": work_session.ended_at,
                "total_seconds": work_session.total_seconds,
                "elapsed_seconds": elapsed_seconds,
            }

        # --------------------------------------------------------
        # RESPONSE
        # --------------------------------------------------------

        response_data = {
            "date": today,

            "work_mode": {
                "code": assignment.task,
                "name": task_display,
            },

            "work_source": work_source,

            "assignment": {
                "id": assignment.id,
                "assignment_date": assignment.assignment_date,
                "assigned_class": assignment.assigned_class,
                "task": assignment.task,
                "instruction": assignment.instruction,
                "has_attachment": bool(
                    assignment.attachment
                ),
                "has_homework_attachment": bool(
                    assignment.homework_attachment
                ),
            },

            "work_session": session_data,
        }

        # --------------------------------------------------------
        # SPECIAL ADDED INFORMATION
        # --------------------------------------------------------

        if special_access is not None:
            response_data["special_added_access"] = {
                "id": special_access.id,
                "status": special_access.status,
                "original_volunteer": (
                    assignment.volunteer.name
                ),
                "original_volunteer_id": (
                    assignment.volunteer.user_id
                ),
            }

        else:
            response_data["special_added_access"] = None

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )