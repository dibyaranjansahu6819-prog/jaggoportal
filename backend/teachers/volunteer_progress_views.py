from django.utils import timezone
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsTeacherVolunteer

from attendance.models import (
    AttendanceSession,
    StudentAttendance,
)

from admin2.models import (
    VolunteerAssignment,
    VolunteerAccountStatus,
)

from .models import (
    Teacher,
    VolunteerWorkSession,
    StudentProgress,
    SpecialAddedWorkAccess,
)
from students.models import StudentHomework
from students.serializers import StudentHomeworkCompletionSerializer

from .volunteer_progress_serializers import (
    StudentProgressSerializer,
)


def get_current_volunteer(request):
    """
    Return the Teacher profile associated with
    the authenticated Django User.
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


def get_account_status(volunteer):
    """
    Return the volunteer account status.

    Older volunteer records without a status object
    are treated as ACTIVE.
    """

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
            "message": (
                "You must request permission from Admin 2 "
                "before you can access your volunteer dashboard."
            ),
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def get_today_assignment(volunteer):
    """
    Return the volunteer's normal successfully sent assignment
    for today.
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
    Return the Special Added work selected by this volunteer
    for today.

    Both ACTIVE and COMPLETED are valid here because student
    progress is recorded after the work session is completed.
    The volunteer must still have a PRESENT SPECIAL_ADDED
    attendance record.
    """

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


def get_today_work_assignment(volunteer):
    """
    Resolve the assignment the volunteer is actually working on.

    Special Added selected work takes priority over the volunteer's
    own normal assignment.

    Returns:
        (assignment, special_added_access)
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
        get_today_assignment(volunteer),
        None,
    )


def get_today_attendance_session():
    """
    Return the latest attendance session created today.

    The date is determined by the backend.
    """

    today = timezone.localdate()

    sessions = (
        AttendanceSession.objects
        .filter(
            session_date=today,
        )
        .order_by("-started_at")
    )

    return sessions.first()


def get_present_student_ids_for_today():
    """
    Return IDs of students who were marked PRESENT
    in today's Admin1 attendance.

    Distinct is used in case there are multiple
    attendance sessions on the same date.
    """

    today = timezone.localdate()

    return set(
        StudentAttendance.objects
        .filter(
            session__session_date=today,
            status="PRESENT",
        )
        .values_list(
            "student_id",
            flat=True,
        )
        .distinct()
    )


class VolunteerProgressStudentsView(APIView):
    """
    Returns students eligible for Track Progress.

    Only:
      - today's teaching assignment
      - assigned class
      - PRESENT students
      - completed work session
    """

    permission_classes = [
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

        assignment, special_access = get_today_work_assignment(volunteer)

        if assignment is None:
            return Response(
                {
                    "assignment": None,
                    "students": [],
                    "message": "No work assigned for today.",
                }
            )

        # Track Progress is only for Teaching.
        if assignment.task != "TEACHING":
            return Response(
                {
                    "assignment": {
                        "id": assignment.id,
                        "class": assignment.assigned_class,
                        "task": assignment.task,
                    },
                    "students": [],
                    "message": (
                        "Track Progress is available only "
                        "for Teaching assignments."
                    ),
                }
            )

        work_session = (
            VolunteerWorkSession.objects
            .filter(
                assignment=assignment,
                volunteer=volunteer,
            )
            .first()
        )

        if work_session is None:
            return Response(
                {
                    "assignment": {
                        "id": assignment.id,
                        "class": assignment.assigned_class,
                        "task": assignment.task,
                    },
                    "students": [],
                    "message": (
                        "Complete today's work before "
                        "tracking student progress."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if work_session.status != "IN_PROGRESS":
            return Response(
                {
                    "assignment": {
                        "id": assignment.id,
                        "class": assignment.assigned_class,
                        "task": assignment.task,
                    },
                    "students": [],
                    "message": (
                        "Start today's Teaching session before "
                        "tracking student progress."
                    ),
                    "work_session_status": (
                        work_session.status
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        present_student_ids = (
            get_present_student_ids_for_today()
        )

        from students.models import Student

        students = Student.objects.filter(
            id__in=present_student_ids,
            group=assignment.assigned_class,
        ).order_by(
            "student_class",
            "name",
        )

        existing_progress = {
            record.student_id: record
            for record in (
                StudentProgress.objects
                .filter(
                    assignment=assignment,
                    volunteer=volunteer,
                )
                .select_related("student")
            )
        }

        data = []

        for student in students:
            progress = existing_progress.get(
                student.id
            )

            data.append(
                {
                    "student_id": student.id,
                    "roll_no": student.roll_no,
                    "name": student.name,
                    "class": student.student_class,
                    "attendance": "PRESENT",
                    "progress": (
                        StudentProgressSerializer(
                            progress
                        ).data
                        if progress
                        else None
                    ),
                }
            )

        return Response(
            {
                "date": timezone.localdate(),
                "assignment": {
                    "id": assignment.id,
                    "class": assignment.assigned_class,
                    "task": assignment.task,
                    "instruction": assignment.instruction,
                },
                "work_session": {
                    "id": work_session.id,
                    "status": work_session.status,
                    "started_at": work_session.started_at,
                    "ended_at": work_session.ended_at,
                    "total_seconds": (
                        work_session.total_seconds
                    ),
                },
                "students": data,
            }
        )


class VolunteerProgressSaveView(APIView):
    """
    Create or update progress for a PRESENT student.

    Expected request:

    {
        "student": 1,
        "performance": "GOOD",
        "feedback": "Excellent participation.",
        "homework_given": true
    }
    """

    permission_classes = [
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

        assignment, special_access = get_today_work_assignment(volunteer)

        if assignment is None:
            return Response(
                {
                    "error": "No work assigned for today."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if assignment.task != "TEACHING":
            return Response(
                {
                    "error": (
                        "Student progress can only be "
                        "recorded for Teaching assignments."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

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
                        "Work session not found. "
                        "Complete today's work first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if work_session.status != "IN_PROGRESS":
            return Response(
                {
                    "error": (
                        "Teaching session must be active "
                        "before recording student progress."
                    ),
                    "work_session_status": (
                        work_session.status
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_id = request.data.get(
            "student"
        )

        if not student_id:
            return Response(
                {
                    "error": "student is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from students.models import Student

        try:
            student = Student.objects.get(
                id=student_id
            )
        except Student.DoesNotExist:
            return Response(
                {
                    "error": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # CLASS VALIDATION
        # -------------------------------------------------

        if (
            student.group
            != assignment.assigned_class
        ):
            return Response(
                {
                    "error": (
                        "This student does not belong "
                        "to your assigned class."
                    ),
                    "code": "STUDENT_CLASS_MISMATCH",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # PRESENT VALIDATION
        # -------------------------------------------------

        present_student_ids = (
            get_present_student_ids_for_today()
        )

        if student.id not in present_student_ids:
            return Response(
                {
                    "error": (
                        "Progress can only be recorded "
                        "for students marked PRESENT today."
                    ),
                    "code": "STUDENT_NOT_PRESENT",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # -------------------------------------------------
        # INPUT VALIDATION
        # -------------------------------------------------

        performance = request.data.get(
            "performance"
        )

        feedback = request.data.get(
            "feedback",
            "",
        )

        homework_given = request.data.get(
            "homework_given"
        )

        if performance not in [
            "POOR",
            "AVERAGE",
            "GOOD",
        ]:
            return Response(
                {
                    "error": (
                        "performance must be "
                        "POOR, AVERAGE, or GOOD."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if homework_given is None:
            return Response(
                {
                    "error": (
                        "homework_given is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(
            homework_given,
            bool,
        ):
            return Response(
                {
                    "error": (
                        "homework_given must be "
                        "true or false."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if feedback is None:
            feedback = ""

        if not isinstance(
            feedback,
            str,
        ):
            return Response(
                {
                    "error": "feedback must be text."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedback = feedback.strip()

        # -------------------------------------------------
        # CREATE / UPDATE
        # -------------------------------------------------

        progress, created = (
            StudentProgress.objects.update_or_create(
                assignment=assignment,
                volunteer=volunteer,
                student=student,
                defaults={
                    "work_session": work_session,
                    "performance": performance,
                    "feedback": feedback,
                    "homework_given": homework_given,
                },
            )
        )

        # Homework is a separate record because completion happens later.
        # Given -> create one PENDING record.
        # Not given -> remove only unfinished PENDING homework.
        # COMPLETED homework is preserved so awarded XP is never revoked.
        homework = (
            StudentHomework.objects
            .filter(
                student=student,
                assignment=assignment,
            )
            .first()
        )

        if homework_given:
            if homework is None:
                homework = StudentHomework.objects.create(
                    student=student,
                    assignment=assignment,
                    work_session=work_session,
                    status="PENDING",
                )
            elif homework.status == "PENDING" and homework.work_session_id != work_session.id:
                homework.work_session = work_session
                homework.save(
                    update_fields=[
                        "work_session",
                        "updated_at",
                    ]
                )
        else:
            if homework is not None and homework.status == "PENDING":
                homework.delete()
                homework = None

        return Response(
            {
                "message": (
                    "Student progress saved."
                    if created
                    else "Student progress updated."
                ),
                "progress": StudentProgressSerializer(
                    progress
                ).data,
                "homework": (
                    StudentHomeworkCompletionSerializer(
                        homework
                    ).data
                    if homework is not None
                    else None
                ),
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )
