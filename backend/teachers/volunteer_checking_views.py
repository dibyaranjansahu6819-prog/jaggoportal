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

from attendance.models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
    Holiday,
)

from students.models import StudentHomework

from .models import (
    Teacher,
    VolunteerWorkSession,
    SpecialAddedWorkAccess,
    StudentChecking,
)

from .volunteer_checking_serializers import StudentCheckingSerializer


# ============================================================
# HELPERS
# ============================================================


def get_current_volunteer(request):
    """
    Return the Teacher profile belonging to the
    currently authenticated Django user.
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
    Return the current volunteer account status.

    Older volunteer records without a status record
    are treated as ACTIVE.
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


def get_today_assignment(volunteer):
    """
    Resolve the assignment the volunteer is actually
    authorized to work on today.

    Priority:
        1. Active Special Added work
        2. Own normal assignment
    """

    today = timezone.localdate()

    # --------------------------------------------------------
    # SPECIAL ADDED WORK
    # --------------------------------------------------------

    special_access = (
        SpecialAddedWorkAccess.objects
        .select_related(
            "assignment",
            "assignment__volunteer",
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

    if special_access is not None:
        return (
            special_access.assignment,
            special_access,
        )

    # --------------------------------------------------------
    # NORMAL ASSIGNMENT
    # --------------------------------------------------------

    assignment = (
        VolunteerAssignment.objects
        .filter(
            volunteer=volunteer,
            assignment_date=today,
            email_status="SENT",
        )
        .first()
    )

    return assignment, None


def get_today_attendance_session():
    """
    Return today's latest attendance session.

    Attendance date is always determined by the backend.
    """

    today = timezone.localdate()

    return (
        AttendanceSession.objects
        .filter(
            session_date=today,
        )
        .order_by("-started_at")
        .first()
    )


def get_present_students(assigned_class):
    """
    Return today's PRESENT students belonging to the
    assignment's group.

    assigned_class is expected to be:
        ClassA
        ClassB
        ClassC
        ClassD
        ClassE
    """

    session = get_today_attendance_session()

    if session is None:
        return StudentAttendance.objects.none()

    return (
        StudentAttendance.objects
        .filter(
            session=session,
            status="PRESENT",
            student__group=assigned_class,
        )
        .select_related(
            "student",
        )
        .order_by(
            "student__roll_no"
        )
    )


def get_actual_work_session(
    assignment,
    volunteer,
):
    """
    Return the work session belonging to the actual volunteer
    performing the assignment.

    This is important for Special Added work because the
    assignment remains owned by the original volunteer while
    the work session belongs to the Special Added volunteer.
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


def validate_checking_assignment(
    assignment,
):
    """
    Ensure the resolved assignment is actually a
    Checking assignment.
    """

    if assignment is None:
        return Response(
            {
                "error": "No work assigned for today.",
                "code": "NO_WORK_ASSIGNED",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if assignment.task != "CHECKING":
        return Response(
            {
                "error": (
                    "Today's assigned work is not "
                    "a Checking assignment."
                ),
                "code": "NOT_CHECKING_ASSIGNMENT",
                "task": assignment.task,
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


def validate_special_added_access(
    special_access,
):
    """
    Validate Special Added authorization.
    """

    if special_access is None:
        return None

    if special_access.status != "ACTIVE":
        return Response(
            {
                "error": (
                    "This Special Added work "
                    "is no longer active."
                ),
                "code": "SPECIAL_ADDED_WORK_INACTIVE",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    attendance = special_access.attendance

    if (
        attendance.status != "PRESENT"
        or attendance.attendance_source != "SPECIAL_ADDED"
    ):
        return Response(
            {
                "error": (
                    "You must be marked Special Added "
                    "and PRESENT before accessing this work."
                ),
                "code": "SPECIAL_ADDED_NOT_PRESENT",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return None


def validate_regular_school_day():
    """
    Checking work is allowed only on a regular class day.
    """

    today = timezone.localdate()

    if Holiday.is_holiday(today):
        holiday = (
            Holiday.objects
            .filter(
                date=today,
                is_active=True,
            )
            .first()
        )

        return Response(
            {
                "error": (
                    "Checking work cannot be performed "
                    "because today is a holiday."
                ),
                "code": "HOLIDAY",
                "holiday_name": (
                    holiday.name
                    if holiday
                    else None
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    daily_status = (
        DailySchoolStatus.objects
        .filter(
            date=today
        )
        .first()
    )

    if (
        daily_status
        and daily_status.status != "REGULAR_CLASS"
    ):
        return Response(
            {
                "error": (
                    "Checking work cannot be performed "
                    "because today is not a regular class day."
                ),
                "code": "NOT_REGULAR_CLASS",
                "school_status": daily_status.status,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def get_student_checking_record(
    assignment,
    volunteer,
    student,
):
    """
    Return the existing checking record for a student.
    """

    return (
        StudentChecking.objects
        .filter(
            assignment=assignment,
            volunteer=volunteer,
            student=student,
        )
        .first()
    )


# ============================================================
# CHECKING DASHBOARD
# ============================================================


class VolunteerCheckingDashboardView(APIView):
    """
    Return today's Checking dashboard.

    Supports:
        - Normal assigned volunteer
        - Special Added volunteer

    The response contains:
        - assignment details
        - work source
        - work session
        - present students
        - checked/pending status
        - checked count
        - total present count
    """

    permission_classes = [
        IsTeacherVolunteer
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

        if (
            get_volunteer_account_status(
                volunteer
            )
            == "REMOVED"
        ):
            return removed_response()

        assignment, special_access = get_today_assignment(
            volunteer
        )

        assignment_error = validate_checking_assignment(
            assignment
        )

        if assignment_error:
            return assignment_error

        special_error = validate_special_added_access(
            special_access
        )

        if special_error:
            return special_error

        work_session = get_actual_work_session(
            assignment,
            volunteer,
        )

        present_records = get_present_students(
            assignment.assigned_class
        )

        students = []

        checked_count = 0

        for attendance_record in present_records:

            student = attendance_record.student

            checking = get_student_checking_record(
                assignment=assignment,
                volunteer=volunteer,
                student=student,
            )

            if checking is not None:
                checked = True
                checked_count += 1
            else:
                checked = False

            students.append(
                {
                    "student": student.id,
                    "name": student.name,
                    "roll_no": student.roll_no,
                    "student_class": student.student_class,
                    "group": student.group,
                    "checked": checked,
                    "checking": (
                        StudentCheckingSerializer(
                            checking
                        ).data
                        if checking
                        else None
                    ),
                }
            )

        response_data = {
            "date": timezone.localdate(),
            "work_source": (
                "SPECIAL_ADDED"
                if special_access
                else "ASSIGNED"
            ),
            "assignment": {
                "id": assignment.id,
                "assignment_date": assignment.assignment_date,
                "assigned_class": assignment.assigned_class,
                "task": assignment.task,
                "instruction": assignment.instruction,
                "attachment": (
                    request.build_absolute_uri(
                        assignment.attachment.url
                    )
                    if assignment.attachment
                    else None
                ),
            },
            "volunteer": {
                "id": volunteer.id,
                "user_id": volunteer.user_id,
                "name": volunteer.name,
                "email": volunteer.email,
                "subject": (
                    volunteer.subject.name
                    if volunteer.subject
                    else None
                ),
            },
            "work_session": (
                {
                    "id": work_session.id,
                    "status": work_session.status,
                    "started_at": work_session.started_at,
                    "ended_at": work_session.ended_at,
                    "total_seconds": work_session.total_seconds,
                }
                if work_session
                else None
            ),
            "students_present": len(students),
            "students_checked": checked_count,
            "students_pending": (
                len(students) - checked_count
            ),
            "students": students,
            "special_added_access": (
                {
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
                if special_access
                else None
            ),
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# CHECKING STUDENT DETAIL
# ============================================================


class VolunteerCheckingStudentDetailView(APIView):
    """
    Return one present student's Checking information.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    def get(self, request, student_id):

        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
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

        assignment, special_access = get_today_assignment(
            volunteer
        )

        assignment_error = validate_checking_assignment(
            assignment
        )

        if assignment_error:
            return assignment_error

        special_error = validate_special_added_access(
            special_access
        )

        if special_error:
            return special_error

        present_records = get_present_students(
            assignment.assigned_class
        )

        attendance_record = (
            present_records
            .filter(
                student_id=student_id
            )
            .select_related("student")
            .first()
        )

        if attendance_record is None:
            return Response(
                {
                    "error": (
                        "This student is not marked "
                        "PRESENT for today's Checking work."
                    ),
                    "code": "STUDENT_NOT_PRESENT",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        student = attendance_record.student

        checking = get_student_checking_record(
            assignment=assignment,
            volunteer=volunteer,
            student=student,
        )

        homework = (
            StudentHomework.objects
            .filter(
                student=student,
                assignment=assignment,
            )
            .first()
        )

        return Response(
            {
                "student": {
                    "id": student.id,
                    "name": student.name,
                    "roll_no": student.roll_no,
                    "student_class": student.student_class,
                    "group": student.group,
                },
                "attendance": {
                    "status": attendance_record.status,
                    "date": timezone.localdate(),
                },
                "homework": {
                    "given": homework is not None,
                    "current_status": (
                        homework.status
                        if homework
                        else None
                    ),
                },
                "checking": (
                    StudentCheckingSerializer(
                        checking
                    ).data
                    if checking
                    else None
                ),
                "checked": checking is not None,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# SAVE CHECKING
# ============================================================


class VolunteerCheckingSaveView(APIView):
    """
    Create or update Checking information for one
    PRESENT student.

    Allowed during an active Checking work session.

    Saves:
        - DONE / NOT_DONE
        - feedback

    Does NOT modify StudentProgress.
    """

    permission_classes = [
        IsTeacherVolunteer
    ]

    @transaction.atomic
    def post(self, request, student_id):

        volunteer = get_current_volunteer(request)

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
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

        assignment, special_access = get_today_assignment(
            volunteer
        )

        assignment_error = validate_checking_assignment(
            assignment
        )

        if assignment_error:
            return assignment_error

        special_error = validate_special_added_access(
            special_access
        )

        if special_error:
            return special_error

        school_day_error = validate_regular_school_day()

        if school_day_error:
            return school_day_error

        # ----------------------------------------------------
        # FIND ACTUAL WORK SESSION
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
                        "Checking work session "
                        "has not been started."
                    ),
                    "code": "WORK_SESSION_NOT_STARTED",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # CHECKING MUST BE ACTIVE
        # ----------------------------------------------------

        if work_session.status != "IN_PROGRESS":
            return Response(
                {
                    "error": (
                        "Checking information can only "
                        "be saved while the work session "
                        "is active."
                    ),
                    "code": "WORK_SESSION_NOT_ACTIVE",
                    "session_status": work_session.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # FIND PRESENT STUDENT
        # ----------------------------------------------------

        attendance_record = (
            get_present_students(
                assignment.assigned_class
            )
            .filter(
                student_id=student_id
            )
            .select_related("student")
            .first()
        )

        if attendance_record is None:
            return Response(
                {
                    "error": (
                        "This student is not marked "
                        "PRESENT for today's Checking work."
                    ),
                    "code": "STUDENT_NOT_PRESENT",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = attendance_record.student

        # ----------------------------------------------------
        # VERIFY STUDENT GROUP
        # ----------------------------------------------------

        if student.group != assignment.assigned_class:
            return Response(
                {
                    "error": (
                        "This student does not belong "
                        "to the assigned group."
                    ),
                    "code": "WRONG_STUDENT_GROUP",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # VERIFY HOMEWORK EXISTS
        # ----------------------------------------------------

        homework = (
            StudentHomework.objects
            .filter(
                student=student,
                assignment=assignment,
            )
            .first()
        )

        if homework is None:
            return Response(
                {
                    "error": (
                        "No homework was given to this "
                        "student for today's assignment."
                    ),
                    "code": "NO_HOMEWORK",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        homework_status = request.data.get(
            "homework_status"
        )

        feedback = request.data.get(
            "feedback",
            "",
        )

        if homework_status not in {
            "DONE",
            "NOT_DONE",
        }:
            return Response(
                {
                    "error": (
                        "Homework status must be "
                        "DONE or NOT_DONE."
                    ),
                    "code": "INVALID_HOMEWORK_STATUS",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if feedback is None:
            feedback = ""

        feedback = str(feedback).strip()

        # ----------------------------------------------------
        # CREATE / UPDATE CHECKING
        # ----------------------------------------------------

        checking, created = (
            StudentChecking.objects
            .select_for_update()
            .get_or_create(
                assignment=assignment,
                volunteer=volunteer,
                student=student,
                defaults={
                    "work_session": work_session,
                    "homework_status": homework_status,
                    "feedback": feedback,
                },
            )
        )

        if not created:

            checking.work_session = work_session
            checking.homework_status = homework_status
            checking.feedback = feedback

            checking.save(
                update_fields=[
                    "work_session",
                    "homework_status",
                    "feedback",
                    "checked_at",
                ]
            )

        return Response(
            {
                "message": (
                    "Student checking saved."
                    if created
                    else "Student checking updated."
                ),
                "created": created,
                "checking": (
                    StudentCheckingSerializer(
                        checking
                    ).data
                ),
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )