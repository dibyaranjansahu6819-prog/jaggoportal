from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Student
from .serializers import StudentRegistrationSerializer
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsTeacherVolunteer
from .models import StudentHomework
from .serializers import StudentHomeworkCompletionSerializer
from .services import sync_homework_xp
from django.db.models import Sum
from rest_framework.generics import RetrieveAPIView

from .models import Student, StudentXPTransaction
from .serializers import (
    StudentXPSerializer,
    StudentLeaderboardSerializer,
)

from teachers.models import SpecialAddedWorkAccess


class StudentRegistrationView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentRegistrationSerializer
    permission_classes = [AllowAny]


class StudentHomeworkCompleteView(APIView):
    """
    Mark a student's homework as completed.

    Only authenticated volunteers can perform this action.
    Completing homework awards +10 XP exactly once.

    A normal assigned volunteer may complete homework for their own
    assignment.

    A Special Added volunteer may also complete homework when the
    homework belongs to the assignment they were authorized to perform
    through SpecialAddedWorkAccess.
    """

    permission_classes = [
        IsAuthenticated,
        IsTeacherVolunteer,
    ]

    def post(self, request, homework_id):
        homework = (
            StudentHomework.objects
            .select_related(
                "student",
                "assignment",
                "work_session",
                "assignment__volunteer",
            )
            .filter(id=homework_id)
            .first()
        )

        if not homework:
            return Response(
                {
                    "error": "Homework record not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        volunteer = getattr(
            request.user,
            "teacher_profile",
            None,
        )

        if volunteer is None:
            return Response(
                {
                    "error": "Volunteer profile not found."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ---------------------------------------------------------
        # AUTHORIZATION
        # ---------------------------------------------------------
        #
        # Normal case:
        #   The volunteer who owns the original assignment completes
        #   its homework.
        #
        # Special Added case:
        #   The original assignment still belongs to the absent
        #   volunteer, but SpecialAddedWorkAccess authorizes another
        #   volunteer to perform that work.
        #
        # The work_session is also checked so the volunteer completing
        # the homework is the volunteer who actually performed the work.
        # ---------------------------------------------------------

        is_original_assignment_owner = (
            homework.assignment.volunteer_id == volunteer.id
        )

        is_work_session_owner = (
            homework.work_session.volunteer_id == volunteer.id
        )

        is_special_added_authorized = (
            SpecialAddedWorkAccess.objects
            .filter(
                assignment=homework.assignment,
                special_volunteer=volunteer,
                status="COMPLETED",
            )
            .exists()
        )

        if not (
            is_original_assignment_owner
            or (
                is_special_added_authorized
                and is_work_session_owner
            )
        ):
            return Response(
                {
                    "error": "You are not authorized to update this homework."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Homework can only be completed after the volunteer
        # has completed the work session.
        if homework.work_session.status != "COMPLETED":
            return Response(
                {
                    "error": "The volunteer work session must be completed first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Already completed:
        # do not create another XP transaction.
        if homework.status == "COMPLETED":
            serializer = StudentHomeworkCompletionSerializer(homework)

            return Response(
                {
                    "message": "Homework is already completed. No additional XP awarded.",
                    "xp_awarded": 0,
                    "homework": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        homework.status = "COMPLETED"
        homework.completed_at = timezone.now()
        homework.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        xp_transaction = sync_homework_xp(homework)

        serializer = StudentHomeworkCompletionSerializer(homework)

        return Response(
            {
                "message": "Homework completed successfully.",
                "xp_awarded": xp_transaction.points if xp_transaction else 0,
                "homework": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class StudentXPView(RetrieveAPIView):
    """
    Return a student's current XP and complete XP transaction history.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    serializer_class = StudentXPSerializer

    def get_object(self):
        student_id = self.kwargs["student_id"]

        return Student.objects.get(id=student_id)

    def retrieve(self, request, *args, **kwargs):
        student = self.get_object()

        transactions = (
            StudentXPTransaction.objects
            .filter(student=student)
            .select_related("homework", "created_by")
            .order_by("-created_at")
        )

        total_xp = (
            transactions.aggregate(
                total=Sum("points")
            )["total"]
            or 0
        )

        data = {
            "student": student,
            "total_xp": total_xp,
            "transaction_count": transactions.count(),
            "transactions": transactions,
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data)


class StudentXPLeaderboardView(APIView):
    """
    Return the student XP leaderboard.

    Ranking is based only on StudentXPTransaction points.
    Attendance has no effect on student XP.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        students = (
            Student.objects
            .annotate(
                total_xp=Sum("xp_transactions__points")
            )
            .order_by(
                "-total_xp",
                "name",
                "id",
            )
        )

        leaderboard = []

        for index, student in enumerate(students, start=1):
            leaderboard.append(
                {
                    "rank": index,
                    "student_id": student.id,
                    "roll_no": student.roll_no,
                    "name": student.name,
                    "student_class": student.student_class,
                    "group": student.group,
                    "school_name": student.school_name,
                    "total_xp": student.total_xp or 0,
                }
            )

        serializer = StudentLeaderboardSerializer(
            leaderboard,
            many=True,
        )

        return Response(
            {
                "count": len(leaderboard),
                "leaderboard": serializer.data,
            }
        )
