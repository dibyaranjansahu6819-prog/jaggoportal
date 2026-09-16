from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin1
from students.models import Student
from teachers.models import Teacher
from admin2.models import (
    VolunteerAccountStatus,
    VolunteerAssignment,
)

from .models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
)

from .serializers import (
    AttendanceSessionSerializer,
    StudentAttendanceSerializer,
    VolunteerAttendanceSerializer,
)


# ============================================================
# ACTIVE ATTENDANCE SESSION
# ============================================================

def get_active_session():
    """
    Return the currently active attendance session.

    If the 10-minute session has expired, automatically
    close it and return None.
    """

    session = (
        AttendanceSession.objects
        .filter(is_active=True)
        .order_by("-started_at")
        .first()
    )

    if session and session.has_expired:
        session.close_if_expired()
        return None

    return session


# ============================================================
# TODAY'S ASSIGNED VOLUNTEERS
# ============================================================

def get_today_assigned_volunteer_ids():
    """
    Return volunteer IDs that have a successfully sent
    Admin 2 assignment for today.
    """

    today = timezone.localdate()

    return set(
        VolunteerAssignment.objects
        .filter(
            assignment_date=today,
            email_status="SENT",
        )
        .values_list(
            "volunteer_id",
            flat=True,
        )
    )


# ============================================================
# TODAY'S ASSIGNED VOLUNTEER TASKS
# ============================================================

def get_today_assigned_volunteer_tasks():
    """
    Return today's successfully sent Admin 2 assignments.

    Result:

        {
            volunteer_id: task
        }

    Example:

        {
            1: "TEACHING",
            2: "CHECKING",
        }

    If multiple assignments currently exist for the same
    volunteer on the same day, the newest assignment is used.
    """

    today = timezone.localdate()

    assignments = (
        VolunteerAssignment.objects
        .filter(
            assignment_date=today,
            email_status="SENT",
        )
        .order_by(
            "volunteer_id",
            "-created_at",
        )
    )

    assignment_tasks = {}

    for assignment in assignments:

        if assignment.volunteer_id not in assignment_tasks:
            assignment_tasks[
                assignment.volunteer_id
            ] = assignment.task

    return assignment_tasks


# ============================================================
# START ATTENDANCE SESSION
# ============================================================

class StartAttendanceSessionView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    @transaction.atomic
    def post(self, request):

        session = get_active_session()

        # ----------------------------------------------------
        # Only one active session at a time
        # ----------------------------------------------------

        if session:

            return Response(
                {
                    "message": (
                        "An attendance session is already active."
                    ),
                    "session": AttendanceSessionSerializer(
                        session
                    ).data,
                }
            )

        # ----------------------------------------------------
        # Backend controls session time
        # ----------------------------------------------------

        now = timezone.now()

        session = AttendanceSession.objects.create(
            admin=request.user,
            expires_at=now + timedelta(minutes=10),
        )

        return Response(
            {
                "message": (
                    "Today's attendance session started."
                ),
                "session": AttendanceSessionSerializer(
                    session
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# CURRENT ATTENDANCE SESSION
# ============================================================

class CurrentAttendanceSessionView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def get(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "session": None,
                    "message": (
                        "No active attendance session."
                    ),
                }
            )

        return Response(
            {
                "session": AttendanceSessionSerializer(
                    session
                ).data,
            }
        )


# ============================================================
# END ATTENDANCE SESSION
# ============================================================

class EndAttendanceSessionView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def post(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "error": (
                        "No active attendance session."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.is_active = False
        session.ended_at = timezone.now()

        session.save(
            update_fields=[
                "is_active",
                "ended_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Attendance session ended."
                ),
                "session": AttendanceSessionSerializer(
                    session
                ).data,
            }
        )


# ============================================================
# STUDENT ATTENDANCE LIST
# ============================================================

class StudentAttendanceListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def get(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "session": None,
                    "students": [],
                }
            )

        students = (
            Student.objects
            .all()
            .order_by(
                "student_class",
                "roll_no",
            )
        )

        records = {
            record.student_id: record
            for record in StudentAttendance.objects.filter(
                session=session
            )
        }

        data = []

        for student in students:

            record = records.get(
                student.id
            )

            data.append(
                {
                    "student_id": student.id,
                    "roll_no": student.roll_no,
                    "name": student.name,
                    "class": student.student_class,
                    "status": (
                        record.status
                        if record
                        else "ABSENT"
                    ),
                }
            )

        return Response(
            {
                "session_id": session.id,
                "date": session.session_date,
                "students": data,
            }
        )


# ============================================================
# SAVE STUDENT ATTENDANCE
# ============================================================

class SaveStudentAttendanceView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    @transaction.atomic
    def post(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "error": (
                        "Attendance session is inactive "
                        "or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_id = request.data.get(
            "student"
        )

        attendance_status = request.data.get(
            "status"
        )

        # ----------------------------------------------------
        # Validate student
        # ----------------------------------------------------

        if not student_id:

            return Response(
                {
                    "error": "student is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate status
        # ----------------------------------------------------

        if attendance_status not in [
            "PRESENT",
            "ABSENT",
        ]:

            return Response(
                {
                    "error": (
                        "status must be PRESENT or ABSENT."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Get student
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Save attendance
        # ----------------------------------------------------

        attendance, created = (
            StudentAttendance.objects.update_or_create(
                session=session,
                student=student,
                defaults={
                    "status": attendance_status,
                },
            )
        )

        return Response(
            {
                "message": (
                    "Student attendance saved."
                ),
                "attendance": StudentAttendanceSerializer(
                    attendance
                ).data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


# ============================================================
# VOLUNTEER LIST
# ============================================================

class VolunteerListView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def get(self, request):

        # ----------------------------------------------------
        # Only volunteers who are not REMOVED are available
        # for Admin 1's "+ Add Volunteer" list.
        #
        # Historical attendance remains untouched.
        # ----------------------------------------------------

        removed_ids = set(
            VolunteerAccountStatus.objects
            .filter(
                status="REMOVED"
            )
            .values_list(
                "volunteer_id",
                flat=True,
            )
        )

        volunteers = (
            Teacher.objects
            .exclude(
                id__in=removed_ids
            )
            .select_related("subject")
            .order_by("name")
        )

        assigned_ids = (
            get_today_assigned_volunteer_ids()
        )

        data = []

        for volunteer in volunteers:

            data.append(
                {
                    "id": volunteer.id,
                    "user_id": volunteer.user_id,
                    "name": volunteer.name,
                    "subject": (
                        volunteer.subject.name
                        if volunteer.subject
                        else None
                    ),
                    "email": volunteer.email,
                    "free_days": volunteer.free_days,
                    "assigned_today": (
                        volunteer.id in assigned_ids
                    ),
                }
            )

        return Response(
            {
                "volunteers": data,
            }
        )


# ============================================================
# CURRENT VOLUNTEER ATTENDANCE
# ============================================================

class CurrentVolunteerAttendanceView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    @transaction.atomic
    def get(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "session": None,
                    "volunteers": [],
                }
            )

        # ----------------------------------------------------
        # Get today's Admin 2 assignments.
        #
        # Only successfully sent assignments count.
        # ----------------------------------------------------

        assignment_tasks = (
            get_today_assigned_volunteer_tasks()
        )

        # ----------------------------------------------------
        # Automatically create attendance records for
        # assigned volunteers.
        #
        # Admin 2 Teaching -> TEACHING
        # Admin 2 Checking -> CHECKING
        #
        # ASSIGNED source is preserved.
        # ----------------------------------------------------

        for volunteer_id, assigned_task in (
            assignment_tasks.items()
        ):

            # -----------------------------------------------
            # Do not create attendance for removed volunteers.
            # -----------------------------------------------

            account_status = (
                VolunteerAccountStatus.objects
                .filter(
                    volunteer_id=volunteer_id
                )
                .first()
            )

            if (
                account_status
                and account_status.status == "REMOVED"
            ):
                continue

            VolunteerAttendance.objects.get_or_create(
                session=session,
                volunteer_id=volunteer_id,
                defaults={
                    "task": assigned_task,
                    "status": "ABSENT",
                    "attendance_source": "ASSIGNED",
                },
            )

        # ----------------------------------------------------
        # Get all attendance records for this session.
        # ----------------------------------------------------

        records = (
            VolunteerAttendance.objects
            .filter(
                session=session
            )
            .select_related(
                "volunteer"
            )
            .order_by(
                "volunteer__name"
            )
        )

        return Response(
            {
                "session_id": session.id,
                "date": session.session_date,
                "volunteers": (
                    VolunteerAttendanceSerializer(
                        records,
                        many=True,
                    ).data
                ),
            }
        )


# ============================================================
# ADD VOLUNTEER MANUALLY
# ============================================================

class AddVolunteerAttendanceView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    @transaction.atomic
    def post(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "error": (
                        "Attendance session is inactive "
                        "or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        volunteer_id = request.data.get(
            "volunteer"
        )

        task = request.data.get(
            "task"
        )

        # ----------------------------------------------------
        # Validate volunteer ID
        # ----------------------------------------------------

        if not volunteer_id:

            return Response(
                {
                    "error": (
                        "volunteer is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate task
        # ----------------------------------------------------

        if task not in [
            "TEACHING",
            "CHECKING",
        ]:

            return Response(
                {
                    "error": (
                        "task must be TEACHING or CHECKING."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Get volunteer
        # ----------------------------------------------------

        try:

            volunteer = Teacher.objects.get(
                id=volunteer_id
            )

        except Teacher.DoesNotExist:

            return Response(
                {
                    "error": "Volunteer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ====================================================
        # IMPORTANT REMOVED-VOLUNTEER PROTECTION
        # ====================================================

        account_status = (
            VolunteerAccountStatus.objects
            .filter(
                volunteer=volunteer
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
                        "This volunteer has been removed "
                        "by Admin 2 and cannot be added "
                        "to attendance."
                    ),
                    "code": "VOLUNTEER_REMOVED",
                    "message": (
                        "The volunteer must receive "
                        "Admin 2 permission before "
                        "access can be restored."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ====================================================
        # SPECIAL ADDED ATTENDANCE
        # ====================================================

        attendance, created = (
            VolunteerAttendance.objects.get_or_create(
                session=session,
                volunteer=volunteer,
                defaults={
                    "task": task,
                    "status": "ABSENT",
                    "attendance_source": "SPECIAL_ADDED",
                },
            )
        )

        # ----------------------------------------------------
        # Prevent duplicate volunteer
        # ----------------------------------------------------

        if not created:

            return Response(
                {
                    "error": (
                        "Volunteer already exists "
                        "in this session."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Volunteer added.",
                "attendance": (
                    VolunteerAttendanceSerializer(
                        attendance
                    ).data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# SAVE VOLUNTEER ATTENDANCE
# ============================================================

class SaveVolunteerAttendanceView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    @transaction.atomic
    def post(self, request):

        session = get_active_session()

        if not session:

            return Response(
                {
                    "error": (
                        "Attendance session is inactive "
                        "or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        volunteer_id = request.data.get(
            "volunteer"
        )

        attendance_status = request.data.get(
            "status"
        )

        task = request.data.get(
            "task"
        )

        # ----------------------------------------------------
        # Validate volunteer
        # ----------------------------------------------------

        if not volunteer_id:

            return Response(
                {
                    "error": (
                        "volunteer is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate status
        # ----------------------------------------------------

        if attendance_status not in [
            "PRESENT",
            "ABSENT",
        ]:

            return Response(
                {
                    "error": (
                        "status must be PRESENT or ABSENT."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Validate task
        # ----------------------------------------------------

        if task not in [
            "TEACHING",
            "CHECKING",
        ]:

            return Response(
                {
                    "error": (
                        "task must be TEACHING or CHECKING."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Find existing attendance
        # ----------------------------------------------------

        try:

            attendance = (
                VolunteerAttendance.objects.get(
                    session=session,
                    volunteer_id=volunteer_id,
                )
            )

        except VolunteerAttendance.DoesNotExist:

            return Response(
                {
                    "error": (
                        "Volunteer has not been added "
                        "to this session."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ----------------------------------------------------
        # Update attendance
        # ----------------------------------------------------

        attendance.task = task
        attendance.status = attendance_status

        # ----------------------------------------------------
        # DO NOT change attendance_source.
        #
        # ASSIGNED stays ASSIGNED.
        # SPECIAL_ADDED stays SPECIAL_ADDED.
        #
        # This is required for correct XP calculation.
        # ----------------------------------------------------

        attendance.save()

        return Response(
            {
                "message": (
                    "Volunteer attendance saved."
                ),
                "attendance": (
                    VolunteerAttendanceSerializer(
                        attendance
                    ).data
                ),
            }
        )


# ============================================================
# TODAY ATTENDANCE SUMMARY
# ============================================================

class TodayAttendanceSummaryView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def get(self, request):

        today = timezone.localdate()

        sessions = (
            AttendanceSession.objects
            .filter(
                admin=request.user,
                session_date=today,
            )
            .order_by(
                "-started_at"
            )
        )

        session = sessions.first()

        if not session:

            return Response(
                {
                    "date": today,
                    "session": None,
                    "students": [],
                    "volunteers": [],
                }
            )

        students = (
            StudentAttendance.objects
            .filter(
                session=session
            )
            .select_related(
                "student"
            )
        )

        volunteers = (
            VolunteerAttendance.objects
            .filter(
                session=session
            )
            .select_related(
                "volunteer"
            )
        )

        return Response(
            {
                "date": today,
                "session": (
                    AttendanceSessionSerializer(
                        session
                    ).data
                ),
                "students": (
                    StudentAttendanceSerializer(
                        students,
                        many=True,
                    ).data
                ),
                "volunteers": (
                    VolunteerAttendanceSerializer(
                        volunteers,
                        many=True,
                    ).data
                ),
            }
        )


# ============================================================
# ATTENDANCE HISTORY
# ============================================================

class AttendanceHistoryView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin1,
    ]

    def get(self, request):

        sessions = (
            AttendanceSession.objects
            .filter(
                admin=request.user
            )
            .order_by(
                "-session_date",
                "-started_at",
            )
        )

        return Response(
            {
                "sessions": (
                    AttendanceSessionSerializer(
                        sessions,
                        many=True,
                    ).data
                ),
            }
        )