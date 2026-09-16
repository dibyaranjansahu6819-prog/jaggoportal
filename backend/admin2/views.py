import io
import textwrap

from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.http import HttpResponse

from PIL import Image, ImageDraw, ImageFont

from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin2
from attendance.models import (
    StudentAttendance,
    VolunteerAttendance,
)
from students.models import Student
from teachers.models import Teacher

from .models import (
    VolunteerAccountStatus,
    VolunteerAccessRequest,
    VolunteerAssignment,
    VolunteerCaution,
    VolunteerXPTransaction,
)
from .serializers import (
    AccessRequestSerializer,
    ManualXPSerializer,
    SendAssignmentSerializer,
    StudentSummarySerializer,
    VolunteerAccountStatusSerializer,
    VolunteerAssignmentSerializer,
    VolunteerCautionSerializer,
    VolunteerListSerializer,
    XPTransactionSerializer,
)
from .services import (
    get_assigned_absence_streak,
    get_current_status,
    get_volunteer_xp,
)


class Admin2BaseView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdmin2,
    ]


class Admin2DashboardView(Admin2BaseView):

    def get(self, request):
        today = timezone.localdate()

        total_students = Student.objects.count()

        present_students = (
            StudentAttendance.objects.filter(
                session__session_date=today,
                status="PRESENT",
            )
            .values("student_id")
            .distinct()
            .count()
        )

        assignments = VolunteerAssignment.objects.filter(
            assignment_date=today
        ).select_related(
            "volunteer",
            "created_by",
        )

        caution_count = VolunteerCaution.objects.filter(
            status="ACTIVE"
        ).count()

        pending_access = VolunteerAccessRequest.objects.filter(
            status="PENDING"
        ).count()

        return Response(
            {
                "date": today,
                "students": {
                    "total_registered": total_students,
                    "present_today": present_students,
                },
                "volunteers": {
                    "registered": Teacher.objects.count(),
                },
                "assignments_today": assignments.count(),
                "active_cautions": caution_count,
                "pending_access_requests": pending_access,
            }
        )


class TotalStudentsView(Admin2BaseView):

    def get(self, request):
        students = Student.objects.all().order_by(
            "student_class",
            "roll_no",
        )

        return Response(
            {
                "count": students.count(),
                "students": StudentSummarySerializer(
                    students,
                    many=True,
                ).data,
            }
        )


class PresentStudentsTodayView(Admin2BaseView):

    def get(self, request):
        today = timezone.localdate()

        student_ids = (
            StudentAttendance.objects.filter(
                session__session_date=today,
                status="PRESENT",
            )
            .values_list(
                "student_id",
                flat=True,
            )
            .distinct()
        )

        students = Student.objects.filter(
            id__in=student_ids
        ).order_by(
            "student_class",
            "roll_no",
        )

        return Response(
            {
                "date": today,
                "count": students.count(),
                "students": StudentSummarySerializer(
                    students,
                    many=True,
                ).data,
            }
        )


class RegisteredVolunteersView(Admin2BaseView):

    def get(self, request):
        volunteers = Teacher.objects.all().select_related(
            "course",
            "subject",
        ).order_by("name")

        return Response(
            {
                "count": volunteers.count(),
                "volunteers": VolunteerListSerializer(
                    volunteers,
                    many=True,
                ).data,
            }
        )


class TodayAssignmentsView(Admin2BaseView):

    def get(self, request):
        today = timezone.localdate()

        assignments = VolunteerAssignment.objects.filter(
            assignment_date=today
        ).select_related(
            "volunteer",
            "created_by",
        )

        return Response(
            {
                "date": today,
                "count": assignments.count(),
                "assignments": VolunteerAssignmentSerializer(
                    assignments,
                    many=True,
                ).data,
            }
        )


class AssignmentHistoryView(Admin2BaseView):

    def get(self, request):
        assignments = VolunteerAssignment.objects.all().select_related(
            "volunteer",
            "created_by",
        )

        return Response(
            {
                "count": assignments.count(),
                "assignments": VolunteerAssignmentSerializer(
                    assignments,
                    many=True,
                ).data,
            }
        )


class SendAssignmentView(Admin2BaseView):

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    @transaction.atomic
    def post(self, request):
        serializer = SendAssignmentSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        volunteer = serializer.validated_data[
            "volunteer"
        ]

        assignment = VolunteerAssignment(
            volunteer=volunteer,
            assignment_date=timezone.localdate(),
            assigned_class=serializer.validated_data[
                "assigned_class"
            ],
            task=serializer.validated_data[
                "task"
            ],
            instruction=serializer.validated_data.get(
                "instruction",
                "",
            ),
            attachment=serializer.validated_data.get(
                "attachment"
            ),
            sender_email="",
            created_by=request.user,
        )

        assignment.full_clean()

        class_name = (
            assignment.get_assigned_class_display()
        )

        task_name = (
            assignment.get_task_display()
        )

        subject = (
            "Jaago Team - Volunteer Assignment - "
            f"{class_name}"
        )

        body = (
            f"Hello {volunteer.name},\n\n"
            "You have been assigned the following task "
            f"for {assignment.assignment_date}.\n\n"
            f"Class: {class_name}\n"
            f"Task: {task_name}\n\n"
            "Instruction / Details:\n"
            f"{assignment.instruction or 'No additional instructions.'}\n\n"
            "Please follow the assigned instructions.\n\n"
            "Regards, Jaago Team"
        )

        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                to=[volunteer.email],
            )

            if assignment.attachment:
                email.attach_file(
                    assignment.attachment.path
                )

            email.send(
                fail_silently=False
            )

            assignment.email_status = "SENT"
            assignment.email_sent_at = timezone.now()
            assignment.sender_email = (
                getattr(
                    email,
                    "from_email",
                    ""
                )
                or ""
            )

            assignment.save()

        except Exception as exc:
            assignment.email_status = "FAILED"
            assignment.email_error = str(exc)
            assignment.save()

            return Response(
                {
                    "detail": "Email could not be sent.",
                    "error": str(exc),
                    "assignment": VolunteerAssignmentSerializer(
                        assignment
                    ).data,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Assignment sent successfully.",
                "assignment": VolunteerAssignmentSerializer(
                    assignment
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VolunteerXPView(Admin2BaseView):

    def get(self, request, volunteer_id):
        volunteer = Teacher.objects.filter(
            id=volunteer_id
        ).first()

        if not volunteer:
            return Response(
                {
                    "detail": "Volunteer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        transactions = VolunteerXPTransaction.objects.filter(
            volunteer=volunteer
        )

        return Response(
            {
                "volunteer": volunteer.id,
                "user_id": volunteer.user_id,
                "name": volunteer.name,
                "xp": get_volunteer_xp(volunteer),
                "transactions": XPTransactionSerializer(
                    transactions,
                    many=True,
                ).data,
            }
        )


class ManualXPView(Admin2BaseView):

    @transaction.atomic
    def post(self, request):
        serializer = ManualXPSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        volunteer = serializer.validated_data[
            "volunteer"
        ]

        points = serializer.validated_data[
            "points"
        ]

        reason = serializer.validated_data[
            "reason"
        ]

        source = (
            "ADMIN_INCREASE"
            if points > 0
            else "ADMIN_DECREASE"
        )

        transaction_record = (
            VolunteerXPTransaction.objects.create(
                volunteer=volunteer,
                points=points,
                source=source,
                reason=reason,
                created_by=request.user,
            )
        )

        return Response(
            {
                "message": "XP updated successfully.",
                "current_xp": get_volunteer_xp(
                    volunteer
                ),
                "transaction": XPTransactionSerializer(
                    transaction_record
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CautionListView(Admin2BaseView):

    def get(self, request):
        cautions = VolunteerCaution.objects.filter(
            status="ACTIVE"
        ).select_related(
            "volunteer"
        )

        return Response(
            {
                "count": cautions.count(),
                "cautions": VolunteerCautionSerializer(
                    cautions,
                    many=True,
                ).data,
            }
        )


class VolunteerStatusView(Admin2BaseView):

    def get(self, request, volunteer_id):
        volunteer = Teacher.objects.filter(
            id=volunteer_id
        ).first()

        if not volunteer:
            return Response(
                {
                    "detail": "Volunteer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        account_status = get_current_status(
            volunteer
        )

        return Response(
            VolunteerAccountStatusSerializer(
                account_status
            ).data
        )


class RemoveVolunteerView(Admin2BaseView):

    @transaction.atomic
    def post(self, request, volunteer_id):
        volunteer = Teacher.objects.filter(
            id=volunteer_id
        ).first()

        if not volunteer:
            return Response(
                {
                    "detail": "Volunteer not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get(
            "reason",
            "Removed by Admin 2.",
        )

        account_status = get_current_status(
            volunteer
        )

        account_status.status = "REMOVED"
        account_status.removed_at = timezone.now()
        account_status.removed_by = request.user
        account_status.removal_reason = reason

        account_status.save()

        if volunteer.auth_user:
            volunteer.auth_user.is_active = False
            volunteer.auth_user.save(
                update_fields=["is_active"]
            )

        return Response(
            {
                "message": (
                    "Volunteer removed successfully."
                ),
                "status": "REMOVED",
                "volunteer": volunteer.user_id,
            }
        )


class AccessRequestListView(Admin2BaseView):

    def get(self, request):
        requests = VolunteerAccessRequest.objects.filter(
            status="PENDING"
        ).select_related(
            "volunteer"
        )

        return Response(
            {
                "count": requests.count(),
                "requests": AccessRequestSerializer(
                    requests,
                    many=True,
                ).data,
            }
        )


class DecideAccessRequestView(Admin2BaseView):

    @transaction.atomic
    def post(self, request, request_id):
        access_request = (
            VolunteerAccessRequest.objects
            .select_related("volunteer")
            .filter(id=request_id)
            .first()
        )

        if not access_request:
            return Response(
                {
                    "detail": (
                        "Access request not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if access_request.status != "PENDING":
            return Response(
                {
                    "detail": (
                        "This access request has "
                        "already been decided."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = str(
            request.data.get(
                "decision",
                ""
            )
        ).upper()

        if decision not in [
            "APPROVED",
            "DENIED",
        ]:
            return Response(
                {
                    "detail": (
                        "Decision must be APPROVED "
                        "or DENIED."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = request.data.get(
            "decision_note",
            "",
        )

        access_request.status = decision
        access_request.decided_at = timezone.now()
        access_request.decided_by = request.user
        access_request.decision_note = note

        access_request.save()

        if decision == "APPROVED":
            account_status = get_current_status(
                access_request.volunteer
            )

            account_status.status = "ACTIVE"
            account_status.removed_at = None
            account_status.removed_by = None

            account_status.save()

            if access_request.volunteer.auth_user:
                access_request.volunteer.auth_user.is_active = True
                access_request.volunteer.auth_user.save(
                    update_fields=["is_active"]
                )

        return Response(
            {
                "message": (
                    "Access request "
                    f"{decision.lower()}."
                ),
                "request": AccessRequestSerializer(
                    access_request
                ).data,
            }
        )


class DailyReportPNGView(Admin2BaseView):
    """
    Generate a PNG report containing today's Admin 2 dashboard
    information and volunteer assignments.
    """

    def get(self, request):
        today = timezone.localdate()

        total_students = Student.objects.count()

        present_students = (
            StudentAttendance.objects.filter(
                session__session_date=today,
                status="PRESENT",
            )
            .values("student_id")
            .distinct()
            .count()
        )

        total_volunteers = Teacher.objects.count()

        assignments = list(
            VolunteerAssignment.objects.filter(
                assignment_date=today
            )
            .select_related(
                "volunteer",
                "created_by",
            )
            .order_by(
                "volunteer__name",
                "assigned_class",
            )
        )

        width = 1400
        margin = 60

        try:
            title_font = ImageFont.truetype(
                "arialbd.ttf",
                42,
            )
            section_font = ImageFont.truetype(
                "arialbd.ttf",
                28,
            )
            normal_font = ImageFont.truetype(
                "arial.ttf",
                22,
            )
            small_font = ImageFont.truetype(
                "arial.ttf",
                18,
            )
        except OSError:
            title_font = ImageFont.load_default()
            section_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        header_height = 190
        summary_height = 180
        assignment_count = max(len(assignments), 1)
        assignment_height = assignment_count * 170
        footer_height = 90

        height = (
            header_height
            + summary_height
            + assignment_height
            + footer_height
        )

        image = Image.new(
            "RGB",
            (width, height),
            "white",
        )

        draw = ImageDraw.Draw(image)

        y = 45

        draw.text(
            (margin, y),
            "JAAGO PORTAL",
            fill="black",
            font=title_font,
        )

        y += 60

        draw.text(
            (margin, y),
            "Admin 2 Daily Report",
            fill="black",
            font=section_font,
        )

        y += 45

        draw.text(
            (margin, y),
            f"Date: {today}",
            fill="black",
            font=normal_font,
        )

        y += 55

        draw.line(
            (
                margin,
                y,
                width - margin,
                y,
            ),
            fill="black",
            width=3,
        )

        y += 35

        draw.text(
            (margin, y),
            "Today's Summary",
            fill="black",
            font=section_font,
        )

        y += 50

        summary_items = [
            f"Total Students: {total_students}",
            f"Present Students: {present_students}",
            f"Registered Volunteers: {total_volunteers}",
            f"Today's Assignments: {len(assignments)}",
        ]

        summary_x_positions = [
            margin,
            390,
            720,
            1050,
        ]

        for index, item in enumerate(summary_items):
            x = summary_x_positions[index]

            draw.rectangle(
                (
                    x,
                    y,
                    x + 290,
                    y + 70,
                ),
                outline="black",
                width=2,
            )

            for line_index, line in enumerate(
                textwrap.wrap(item, width=25)
            ):
                draw.text(
                    (
                        x + 12,
                        y + 15 + line_index * 24,
                    ),
                    line,
                    fill="black",
                    font=small_font,
                )

        y += 110

        draw.text(
            (margin, y),
            "Today's Volunteer Assignments",
            fill="black",
            font=section_font,
        )

        y += 55

        columns = [
            ("Volunteer", margin, 300),
            ("Class", 380, 150),
            ("Task", 550, 180),
            ("Instruction / Details", 750, 430),
            ("Email", 1190, 150),
        ]

        for title, x, column_width in columns:
            draw.rectangle(
                (
                    x,
                    y,
                    x + column_width,
                    y + 55,
                ),
                outline="black",
                width=2,
            )

            draw.text(
                (x + 10, y + 15),
                title,
                fill="black",
                font=small_font,
            )

        y += 55

        if assignments:
            for assignment in assignments:
                row_height = 170

                values = [
                    (
                        assignment.volunteer.name,
                        margin,
                        300,
                    ),
                    (
                        assignment.get_assigned_class_display(),
                        380,
                        150,
                    ),
                    (
                        assignment.get_task_display(),
                        550,
                        180,
                    ),
                    (
                        assignment.instruction
                        or "No additional instructions.",
                        750,
                        430,
                    ),
                    (
                        assignment.get_email_status_display(),
                        1190,
                        150,
                    ),
                ]

                for value, x, column_width in values:
                    draw.rectangle(
                        (
                            x,
                            y,
                            x + column_width,
                            y + row_height,
                        ),
                        outline="black",
                        width=2,
                    )

                    wrapped_lines = textwrap.wrap(
                        str(value),
                        width=max(
                            10,
                            int(column_width / 11),
                        ),
                    )

                    text_y = y + 12

                    for line in wrapped_lines[:6]:
                        draw.text(
                            (
                                x + 10,
                                text_y,
                            ),
                            line,
                            fill="black",
                            font=small_font,
                        )
                        text_y += 24

                y += row_height
        else:
            draw.rectangle(
                (
                    margin,
                    y,
                    width - margin,
                    y + 100,
                ),
                outline="black",
                width=2,
            )

            draw.text(
                (
                    margin + 20,
                    y + 30,
                ),
                "No volunteer assignments for today.",
                fill="black",
                font=normal_font,
            )

            y += 120

        y += 20

        draw.line(
            (
                margin,
                y,
                width - margin,
                y,
            ),
            fill="black",
            width=2,
        )

        y += 25

        draw.text(
            (margin, y),
            "Generated by Jaago Portal - Admin 2",
            fill="black",
            font=small_font,
        )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="image/png",
        )

        response["Content-Disposition"] = (
            f'attachment; filename="jaago_admin2_report_{today}.png"'
        )

        return response