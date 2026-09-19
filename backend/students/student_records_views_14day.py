from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import AttendanceSession, Holiday, StudentAttendance
from .models import Student, StudentHomework, StudentXPTransaction
from .serializers_14day import (
    Student14DayHistorySerializer,
    Student14DayRecordSerializer,
)


class Student14DayHistoryView(APIView):
    """
    Return a rolling 14-calendar-day record for one student.

    The period includes today and the previous 13 calendar days.

    Attendance status:
    - PRESENT: a StudentAttendance record exists with PRESENT.
    - ABSENT: a StudentAttendance record exists with ABSENT.
    - HOLIDAY: an active Holiday exists for that date.
    - NO_RECORD: no holiday and no attendance session/record exists.

    Homework is calculated from StudentHomework records whose assignment
    date falls on the corresponding calendar date.

    Student XP is calculated from StudentXPTransaction records created
    on the corresponding calendar date.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = (
            Student.objects
            .filter(id=student_id)
            .first()
        )

        if not student:
            return Response(
                {"error": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        today = timezone.localdate()
        start_date = today - timedelta(days=13)

        attendance_sessions = {
            session.session_date: session
            for session in (
                AttendanceSession.objects
                .filter(
                    session_date__gte=start_date,
                    session_date__lte=today,
                )
                .order_by("session_date", "-started_at")
            )
        }

        attendance_records = {
            record.session.session_date: record
            for record in (
                StudentAttendance.objects
                .filter(
                    student=student,
                    session__session_date__gte=start_date,
                    session__session_date__lte=today,
                )
                .select_related("session")
                .order_by("-session__started_at")
            )
        }

        holidays = {
            holiday.date: holiday
            for holiday in (
                Holiday.objects
                .filter(
                    date__gte=start_date,
                    date__lte=today,
                    is_active=True,
                )
            )
        }

        homework_records = list(
            StudentHomework.objects
            .filter(
                student=student,
                assignment__assignment_date__gte=start_date,
                assignment__assignment_date__lte=today,
            )
            .select_related("assignment")
        )

        homework_by_date = {}
        for homework in homework_records:
            assignment_date = homework.assignment.assignment_date
            homework_by_date.setdefault(assignment_date, []).append(homework)

        xp_records = (
            StudentXPTransaction.objects
            .filter(
                student=student,
                created_at__date__gte=start_date,
                created_at__date__lte=today,
            )
        )

        xp_by_date = {}
        for transaction in xp_records:
            transaction_date = timezone.localtime(
                transaction.created_at
            ).date()
            xp_by_date.setdefault(transaction_date, []).append(transaction)

        records = []

        for offset in range(14):
            current_date = start_date + timedelta(days=offset)

            session = attendance_sessions.get(current_date)
            attendance = attendance_records.get(current_date)
            holiday = holidays.get(current_date)

            if holiday:
                attendance_status = "HOLIDAY"
                session_id = None
            elif attendance:
                attendance_status = attendance.status
                session_id = attendance.session_id
            else:
                attendance_status = "NO_RECORD"
                session_id = session.id if session else None

            daily_homework = homework_by_date.get(current_date, [])
            completed_count = sum(
                1 for item in daily_homework
                if item.status == "COMPLETED"
            )
            pending_count = sum(
                1 for item in daily_homework
                if item.status == "PENDING"
            )

            daily_xp = sum(
                transaction.points
                for transaction in xp_by_date.get(current_date, [])
            )

            homework_xp = sum(
                transaction.points
                for transaction in xp_by_date.get(current_date, [])
                if transaction.source == "HOMEWORK_COMPLETED"
            )

            records.append(
                {
                    "date": current_date,
                    "day": current_date.strftime("%A"),
                    "attendance_status": attendance_status,
                    "session_id": session_id,
                    "holiday_name": (
                        holiday.name if holiday else None
                    ),
                    "homework_total": len(daily_homework),
                    "homework_completed": completed_count,
                    "homework_pending": pending_count,
                    "homework_xp": homework_xp,
                    "total_xp_earned": daily_xp,
                    "is_today": current_date == today,
                }
            )

        payload = {
            "student": {
                "id": student.id,
                "roll_no": student.roll_no,
                "name": student.name,
                "student_class": student.student_class,
                "group": student.group,
                "school_name": student.school_name,
            },
           "period": {
                "start_date": str(start_date),
                "end_date": str(today),
                "days": 14,
            },
            "records": records,
        }

        serializer = Student14DayHistorySerializer(payload)

        return Response(serializer.data)
