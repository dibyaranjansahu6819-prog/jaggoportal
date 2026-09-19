from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsTeacherVolunteer

from admin2.models import (
    VolunteerAssignment,
    VolunteerAccountStatus,
    DailySchoolStatus,
)

from attendance.models import VolunteerAttendance

from .models import (
    Teacher,
    VolunteerWorkSession,
    SpecialAddedWorkAccess,
)

from .volunteer_serializers import (
    VolunteerWorkSessionSerializer,
    VolunteerAssignmentDashboardSerializer,
)


# ============================================================
# VOLUNTEER HELPERS
# ============================================================


def get_current_volunteer(request):
    """
    Return the Teacher profile belonging to the logged-in user.
    """

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
    """
    Return the volunteer account status.

    If an older volunteer does not yet have a status record,
    treat the account as ACTIVE.
    """

    account_status = (
        VolunteerAccountStatus.objects
        .filter(
            volunteer=volunteer
        )
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
            "message": (
                "You must request permission from Admin 2 "
                "before you can access your volunteer dashboard."
            ),
        },
        status=status.HTTP_403_FORBIDDEN,
    )


# ============================================================
# NORMAL / SPECIAL ADDED WORK RESOLUTION
# ============================================================


def get_today_own_assignment(volunteer):
    """
    Return the volunteer's own successfully sent assignment
    for today.

    This is the normal volunteer flow.
    """

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
    """
    Return the active Special Added Work Access for today.

    The Special Added volunteer must have:

        attendance_source = SPECIAL_ADDED
        status = PRESENT

    The selected assignment must still be a successfully sent
    assignment for today.
    """

    today = timezone.localdate()

    access = (
        SpecialAddedWorkAccess.objects
        .select_related(
            "assignment",
            "assignment__volunteer",
            "assignment__created_by",
            "attendance",
        )
        .filter(
            special_volunteer=volunteer,
            access_date=today,
            status="ACTIVE",
            assignment__assignment_date=today,
            assignment__email_status="SENT",
            attendance__volunteer=volunteer,
            attendance__attendance_source="SPECIAL_ADDED",
            attendance__status="PRESENT",
        )
        .first()
    )

    return access


def get_today_work_assignment(volunteer):
    """
    Resolve which assignment the logged-in volunteer is
    actually allowed to work on today.

    Priority:

    1. Active Special Added selected work
    2. Own normal assignment

    Returns:

        assignment
        access

    where access is None for normal work.
    """

    special_access = get_today_special_added_access(
        volunteer
    )

    if special_access is not None:
        return (
            special_access.assignment,
            special_access,
        )

    return (
        get_today_own_assignment(volunteer),
        None,
    )


def get_today_work_session(
    assignment,
    volunteer,
):
    """
    Return the work session belonging to the actual volunteer
    performing the assignment.
    """

    if assignment is None:
        return None

    return (
        VolunteerWorkSession.objects
        .filter(
            assignment=assignment,
            volunteer=volunteer,
        )
        .first()
    )


def serialize_work_assignment(
    assignment,
    volunteer,
    request,
):
    """
    Serialize an assignment together with the actual volunteer's
    work session.

    This is important for Special Added work because:

        assignment.volunteer

    remains the original assigned volunteer, while:

        work_session.volunteer

    is the Special Added volunteer actually performing the work.
    """

    if assignment is None:
        return None

    work_session = get_today_work_session(
        assignment=assignment,
        volunteer=volunteer,
    )

    data = VolunteerAssignmentDashboardSerializer(
        assignment,
        context={
            "request": request,
        },
    ).data

    data["work_session"] = (
        VolunteerWorkSessionSerializer(
            work_session
        ).data
        if work_session
        else None
    )

    return data


# ============================================================
# VOLUNTEER DASHBOARD
# ============================================================


class VolunteerDashboardView(APIView):
    """
    Main volunteer dashboard API.

    Normal volunteer:
        Shows own assignment.

    Special Added volunteer:
        Shows the selected Special Added assignment.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    def get(self, request):

        volunteer = get_current_volunteer(
            request
        )

        if volunteer is None:
            return Response(
                {
                    "error": (
                        "Volunteer profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            get_volunteer_account_status(
                volunteer
            )
            == "REMOVED"
        ):
            return removed_response()

        today = timezone.localdate()

        daily_status = (
            DailySchoolStatus.objects
            .filter(
                date=today
            )
            .first()
        )

        assignment, special_access = (
            get_today_work_assignment(
                volunteer
            )
        )

        assignment_data = serialize_work_assignment(
            assignment=assignment,
            volunteer=volunteer,
            request=request,
        )

        response_data = {
            "volunteer": {
                "id": volunteer.id,
                "user_id": volunteer.user_id,
                "name": volunteer.name,
                "subject": (
                    volunteer.subject.name
                    if volunteer.subject
                    else None
                ),
                "email": volunteer.email,
                "whatsapp_number": (
                    volunteer.whatsapp_number
                ),
            },
            "date": today,
            "school_status": (
                daily_status.status
                if daily_status
                else "REGULAR_CLASS"
            ),
            "assignment": assignment_data,
            "message": (
                "No work assigned for today."
                if assignment_data is None
                else None
            ),
        }

        if special_access is not None:
            response_data["work_source"] = (
                "SPECIAL_ADDED"
            )

            response_data["special_added_access"] = {
                "id": special_access.id,
                "status": special_access.status,
                "original_volunteer": (
                    special_access.assignment
                    .volunteer.name
                ),
                "original_volunteer_id": (
                    special_access.assignment
                    .volunteer.user_id
                ),
            }

        else:
            response_data["work_source"] = (
                "ASSIGNED"
            )

            response_data["special_added_access"] = None

        return Response(
            response_data
        )


# ============================================================
# TODAY'S ASSIGNMENT
# ============================================================


class VolunteerTodayAssignmentView(APIView):
    """
    Return today's actual work for the logged-in volunteer.

    Normal volunteer:
        Own assignment.

    Special Added volunteer:
        Selected Special Added assignment.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    def get(self, request):

        volunteer = get_current_volunteer(
            request
        )

        if volunteer is None:
            return Response(
                {
                    "error": (
                        "Volunteer profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            get_volunteer_account_status(
                volunteer
            )
            == "REMOVED"
        ):
            return removed_response()

        today = timezone.localdate()

        assignment, special_access = (
            get_today_work_assignment(
                volunteer
            )
        )

        if assignment is None:
            return Response(
                {
                    "assignment": None,
                    "message": (
                        "No work assigned for today."
                    ),
                    "date": today,
                    "work_source": "NONE",
                    "special_added_access": None,
                }
            )

        data = serialize_work_assignment(
            assignment=assignment,
            volunteer=volunteer,
            request=request,
        )

        response_data = {
            "assignment": data,
            "date": today,
            "work_source": (
                "SPECIAL_ADDED"
                if special_access
                else "ASSIGNED"
            ),
        }

        if special_access is not None:
            response_data[
                "special_added_access"
            ] = {
                "id": special_access.id,
                "status": special_access.status,
                "original_volunteer": (
                    special_access.assignment
                    .volunteer.name
                ),
                "original_volunteer_id": (
                    special_access.assignment
                    .volunteer.user_id
                ),
            }

        else:
            response_data[
                "special_added_access"
            ] = None

        return Response(
            response_data
        )


# ============================================================
# START WORK SESSION
# ============================================================


class VolunteerWorkSessionStartView(APIView):
    """
    Start today's actual work.

    Normal volunteer:
        Starts their own assignment.

    Special Added volunteer:
        Starts the assignment they selected through
        SpecialAddedWorkAccess.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    @transaction.atomic
    def post(self, request):

        volunteer = get_current_volunteer(
            request
        )

        if volunteer is None:
            return Response(
                {
                    "error": (
                        "Volunteer profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            get_volunteer_account_status(
                volunteer
            )
            == "REMOVED"
        ):
            return removed_response()

        today = timezone.localdate()

        assignment, special_access = (
            get_today_work_assignment(
                volunteer
            )
        )

        if assignment is None:
            return Response(
                {
                    "error": (
                        "No work assigned for today."
                    ),
                    "code": "NO_WORK_ASSIGNED",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ----------------------------------------------------
        # SPECIAL ADDED VALIDATION
        # ----------------------------------------------------

        if special_access is not None:

            if special_access.status != "ACTIVE":
                return Response(
                    {
                        "error": (
                            "This Special Added work "
                            "is no longer active."
                        ),
                        "code": (
                            "SPECIAL_ADDED_WORK_INACTIVE"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            attendance = (
                special_access.attendance
            )

            if (
                attendance.status != "PRESENT"
                or attendance.attendance_source
                != "SPECIAL_ADDED"
            ):
                return Response(
                    {
                        "error": (
                            "You must be marked "
                            "Special Added and PRESENT "
                            "before starting this work."
                        ),
                        "code": (
                            "SPECIAL_ADDED_NOT_PRESENT"
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # ----------------------------------------------------
        # SCHOOL DAY VALIDATION
        # ----------------------------------------------------

        daily_status = (
            DailySchoolStatus.objects
            .filter(
                date=today
            )
            .first()
        )

        if (
            daily_status
            and daily_status.status
            != "REGULAR_CLASS"
        ):
            return Response(
                {
                    "error": (
                        "Normal volunteer work cannot "
                        "be started because today is "
                        "not a regular class day."
                    ),
                    "school_status": (
                        daily_status.status
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # LOCK ASSIGNMENT
        # ----------------------------------------------------

        assignment = (
            VolunteerAssignment.objects
            .select_for_update()
            .select_related(
                "volunteer",
                "created_by",
            )
            .get(
                id=assignment.id
            )
        )

        # ----------------------------------------------------
        # CREATE / GET WORK SESSION
        # ----------------------------------------------------

        work_session, created = (
            VolunteerWorkSession.objects
            .select_for_update()
            .get_or_create(
                assignment=assignment,
                volunteer=volunteer,
                defaults={
                    "status": "NOT_STARTED",
                },
            )
        )

        # ----------------------------------------------------
        # ALREADY COMPLETED
        # ----------------------------------------------------

        if (
            work_session.status
            == "COMPLETED"
        ):
            return Response(
                {
                    "error": (
                        "Today's work is already complete."
                    ),
                    "code": (
                        "WORK_ALREADY_COMPLETED"
                    ),
                    "work_source": (
                        "SPECIAL_ADDED"
                        if special_access
                        else "ASSIGNED"
                    ),
                    "session": (
                        VolunteerWorkSessionSerializer(
                            work_session
                        ).data
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # ALREADY IN PROGRESS
        # ----------------------------------------------------

        if (
            work_session.status
            == "IN_PROGRESS"
        ):
            return Response(
                {
                    "message": (
                        "Today's work is already "
                        "in progress."
                    ),
                    "work_source": (
                        "SPECIAL_ADDED"
                        if special_access
                        else "ASSIGNED"
                    ),
                    "session": (
                        VolunteerWorkSessionSerializer(
                            work_session
                        ).data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # START SESSION
        # ----------------------------------------------------

        work_session.started_at = (
            timezone.now()
        )

        work_session.status = (
            "IN_PROGRESS"
        )

        work_session.ended_at = None
        work_session.total_seconds = None

        work_session.save(
            update_fields=[
                "started_at",
                "status",
                "ended_at",
                "total_seconds",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Special Added work session "
                    "started."
                    if special_access
                    else "Work session started."
                ),
                "work_source": (
                    "SPECIAL_ADDED"
                    if special_access
                    else "ASSIGNED"
                ),
                "assignment": (
                    VolunteerAssignment.objects
                    .filter(
                        id=assignment.id
                    )
                    .values(
                        "id",
                        "assignment_date",
                        "assigned_class",
                        "task",
                    )
                    .first()
                ),
                "session": (
                    VolunteerWorkSessionSerializer(
                        work_session
                    ).data
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# END WORK SESSION
# ============================================================


class VolunteerWorkSessionEndView(APIView):
    """
    End today's actual work.

    Normal volunteer:
        Ends their own work session.

    Special Added volunteer:
        Ends the work session they started for the
        selected Special Added assignment.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    @transaction.atomic
    def post(self, request):

        volunteer = get_current_volunteer(
            request
        )

        if volunteer is None:
            return Response(
                {
                    "error": (
                        "Volunteer profile not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            get_volunteer_account_status(
                volunteer
            )
            == "REMOVED"
        ):
            return removed_response()

        today = timezone.localdate()

        assignment, special_access = (
            get_today_work_assignment(
                volunteer
            )
        )

        if assignment is None:
            return Response(
                {
                    "error": (
                        "No work assigned for today."
                    ),
                    "code": "NO_WORK_ASSIGNED",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ----------------------------------------------------
        # SPECIAL ADDED VALIDATION
        # ----------------------------------------------------

        if special_access is not None:

            if special_access.status not in [
                "ACTIVE",
                "COMPLETED",
            ]:
                return Response(
                    {
                        "error": (
                            "This Special Added work "
                            "is no longer available."
                        ),
                        "code": (
                            "SPECIAL_ADDED_WORK_INACTIVE"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ----------------------------------------------------
        # FIND ACTUAL VOLUNTEER'S SESSION
        # ----------------------------------------------------

        work_session = (
            VolunteerWorkSession.objects
            .select_for_update()
            .filter(
                assignment=assignment,
                volunteer=volunteer,
            )
            .first()
        )

        if work_session is None:
            return Response(
                {
                    "error": (
                        "Work session has not "
                        "been started."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # ALREADY COMPLETED
        # ----------------------------------------------------

        if (
            work_session.status
            == "COMPLETED"
        ):

            return Response(
                {
                    "message": (
                        "Today's work is already complete."
                    ),
                    "work_source": (
                        "SPECIAL_ADDED"
                        if special_access
                        else "ASSIGNED"
                    ),
                    "session": (
                        VolunteerWorkSessionSerializer(
                            work_session
                        ).data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # MUST BE IN PROGRESS
        # ----------------------------------------------------

        if (
            work_session.status
            != "IN_PROGRESS"
        ):
            return Response(
                {
                    "error": (
                        "Work session has not "
                        "been started."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not work_session.started_at:
            return Response(
                {
                    "error": (
                        "Invalid work session."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # CALCULATE DURATION
        # ----------------------------------------------------

        ended_at = timezone.now()

        total_seconds = max(
            0,
            int(
                (
                    ended_at
                    - work_session.started_at
                ).total_seconds()
            ),
        )

        work_session.ended_at = ended_at
        work_session.total_seconds = (
            total_seconds
        )
        work_session.status = "COMPLETED"

        work_session.save(
            update_fields=[
                "ended_at",
                "total_seconds",
                "status",
                "updated_at",
            ]
        )

        # ----------------------------------------------------
        # SPECIAL ADDED ACCESS COMPLETION
        # ----------------------------------------------------

        if special_access is not None:

            special_access.mark_completed()

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return Response(
            {
                "message": (
                    "Special Added work is complete."
                    if special_access
                    else "Today's work is complete."
                ),
                "work_source": (
                    "SPECIAL_ADDED"
                    if special_access
                    else "ASSIGNED"
                ),
                "session": (
                    VolunteerWorkSessionSerializer(
                        work_session
                    ).data
                ),
                "special_added_access": (
                    {
                        "id": special_access.id,
                        "status": special_access.status,
                    }
                    if special_access
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )