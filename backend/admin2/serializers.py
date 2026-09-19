from django.utils import timezone
from rest_framework import serializers

from students.models import Student
from teachers.models import Teacher

from .models import (
    DailySchoolStatus,
    VolunteerAccountStatus,
    VolunteerAccessRequest,
    VolunteerAssignment,
    VolunteerCaution,
    VolunteerXPTransaction,
)
from .services import get_volunteer_xp


class DailySchoolStatusSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = DailySchoolStatus
        fields = [
            "id",
            "date",
            "status",
            "status_display",
            "playing_day_email_status",
            "playing_day_email_sent_at",
            "playing_day_email_error",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "date",
            "playing_day_email_status",
            "playing_day_email_sent_at",
            "playing_day_email_error",
            "created_by",
            "created_at",
            "updated_at",
        ]


class StudentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "roll_no",
            "name",
            "student_class",
            "school_name",
            "created_at",
        ]


class VolunteerListSerializer(serializers.ModelSerializer):
    xp = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    # Human-readable subject name
    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True,
    )

    class Meta:
        model = Teacher
        fields = [
            "id",
            "user_id",
            "name",
            "course",
            "joining_year",
            "subject",
            "subject_name",
            "email",
            "whatsapp_number",
            "free_days",
            "xp",
            "status",
            "created_at",
        ]

    def get_xp(self, obj):
        return get_volunteer_xp(obj)

    def get_status(self, obj):
        status = VolunteerAccountStatus.objects.filter(
            volunteer=obj
        ).first()

        if not status:
            return "ACTIVE"

        return status.status


class VolunteerAssignmentSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    volunteer_user_id = serializers.CharField(
        source="volunteer.user_id",
        read_only=True,
    )

    # Human-readable volunteer subject
    volunteer_subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    volunteer_email = serializers.EmailField(
        source="volunteer.email",
        read_only=True,
    )

    task_display = serializers.CharField(
        source="get_task_display",
        read_only=True,
    )

    assigned_class_display = serializers.CharField(
        source="get_assigned_class_display",
        read_only=True,
    )

    class Meta:
        model = VolunteerAssignment

        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "volunteer_user_id",
            "volunteer_subject",
            "volunteer_email",
            "assignment_date",
            "assigned_class",
            "assigned_class_display",
            "task",
            "task_display",
            "instruction",
            "attachment",
            "homework_attachment",
            "sender_email",
            "email_status",
            "email_sent_at",
            "email_error",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "assignment_date",
            "sender_email",
            "email_status",
            "email_sent_at",
            "email_error",
            "created_by",
            "created_at",
            "updated_at",
        ]


class SendAssignmentSerializer(serializers.Serializer):
    volunteer = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all()
    )

    assigned_class = serializers.ChoiceField(
        choices=VolunteerAssignment.CLASS_CHOICES
    )

    task = serializers.ChoiceField(
        choices=VolunteerAssignment.TASK_CHOICES
    )

    instruction = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    attachment = serializers.FileField(
        required=False,
        allow_null=True,
    )

    homework_attachment = serializers.FileField(
        required=False,
        allow_null=True,
    )

    def validate_volunteer(self, volunteer):
        """
        Validate that the volunteer:
        1. Is not removed.
        2. Has a registered email.
        3. Is available on today's weekday.
        4. Does not already have an assignment today.
        """

        # -----------------------------------------
        # 1. Check volunteer account status
        # -----------------------------------------
        account_status = VolunteerAccountStatus.objects.filter(
            volunteer=volunteer
        ).first()

        if (
            account_status
            and account_status.status == "REMOVED"
        ):
            raise serializers.ValidationError(
                "This volunteer has been removed and cannot be assigned."
            )

        # -----------------------------------------
        # 2. Volunteer must have an email
        # -----------------------------------------
        if not volunteer.email:
            raise serializers.ValidationError(
                "This volunteer does not have a registered email address."
            )

        # -----------------------------------------
        # 3. Get today's date from backend
        # -----------------------------------------
        today = timezone.localdate()

        weekday = today.strftime("%A")

        # -----------------------------------------
        # 4. Read volunteer free days safely
        # -----------------------------------------
        free_days = volunteer.free_days or []

        if isinstance(free_days, str):
            try:
                import json

                free_days = json.loads(free_days)
            except (TypeError, ValueError):
                free_days = []

        if not isinstance(free_days, list):
            free_days = []

        # -----------------------------------------
        # 5. Sunday is not allowed
        # -----------------------------------------
        if weekday == "Sunday":
            raise serializers.ValidationError(
                "Volunteer assignments are not allowed on Sunday."
            )

        # -----------------------------------------
        # 6. Check volunteer availability
        # -----------------------------------------
        if weekday not in free_days:
            raise serializers.ValidationError(
                f"This volunteer is not available on {weekday}."
            )

        # -----------------------------------------
        # 7. Prevent duplicate daily assignment
        # -----------------------------------------
        daily_status = DailySchoolStatus.objects.filter(
            date=today
        ).first()

        if not daily_status:
            raise serializers.ValidationError(
                "Please select Regular Class in today's school status before assigning a volunteer."
            )

        if daily_status.status != "REGULAR_CLASS":
            raise serializers.ValidationError(
                "Volunteer assignments are allowed only when today's status is Regular Class."
            )

        if VolunteerAssignment.objects.filter(
            volunteer=volunteer,
            assignment_date=today,
        ).exists():
            raise serializers.ValidationError(
                "This volunteer already has an assignment for today."
            )

        return volunteer

    def validate_attachment(self, file):
        if not file:
            return file

        # -----------------------------------------
        # Maximum file size: 10 MB
        # -----------------------------------------
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Attachment must be 10 MB or smaller."
            )

        # -----------------------------------------
        # Allowed file extensions
        # -----------------------------------------
        allowed = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".doc",
            ".docx",
            ".txt",
            ".xls",
            ".xlsx",
        }

        filename = file.name.lower()

        if "." not in filename:
            raise serializers.ValidationError(
                "Invalid file extension."
            )

        extension = "." + filename.rsplit(
            ".",
            1
        )[1]

        if extension not in allowed:
            raise serializers.ValidationError(
                "Unsupported attachment type."
            )

        return file

    def validate_homework_attachment(self, file):
        if not file:
            return file

        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Homework attachment must be 10 MB or smaller."
            )

        allowed = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".doc",
            ".docx",
            ".txt",
            ".xls",
            ".xlsx",
        }

        filename = file.name.lower()
        if "." not in filename:
            raise serializers.ValidationError(
                "Invalid homework file extension."
            )

        extension = "." + filename.rsplit(".", 1)[1]
        if extension not in allowed:
            raise serializers.ValidationError(
                "Unsupported homework attachment type."
            )

        return file


class XPTransactionSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    # Human-readable volunteer subject
    volunteer_subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    class Meta:
        model = VolunteerXPTransaction

        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "volunteer_subject",
            "points",
            "source",
            "reason",
            "attendance",
            "created_by",
            "created_at",
        ]


class ManualXPSerializer(serializers.Serializer):
    volunteer = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all()
    )

    points = serializers.IntegerField()

    reason = serializers.CharField(
        required=True,
        allow_blank=False,
    )

    def validate_points(self, value):
        if value == 0:
            raise serializers.ValidationError(
                "XP adjustment cannot be zero."
            )

        return value


class VolunteerCautionSerializer(serializers.ModelSerializer):
    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    volunteer_user_id = serializers.CharField(
        source="volunteer.user_id",
        read_only=True,
    )

    # Human-readable volunteer subject
    volunteer_subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    volunteer_email = serializers.EmailField(
        source="volunteer.email",
        read_only=True,
    )

    class Meta:
        model = VolunteerCaution

        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "volunteer_user_id",
            "volunteer_subject",
            "volunteer_email",
            "status",
            "absence_streak",
            "caution_date",
            "email_sent",
            "email_sent_at",
            "note",
            "resolved_at",
            "resolved_by",
            "created_at",
            "updated_at",
        ]


class VolunteerAccountStatusSerializer(
    serializers.ModelSerializer
):
    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    volunteer_user_id = serializers.CharField(
        source="volunteer.user_id",
        read_only=True,
    )

    # Human-readable volunteer subject
    volunteer_subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    class Meta:
        model = VolunteerAccountStatus

        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "volunteer_user_id",
            "volunteer_subject",
            "status",
            "removed_at",
            "removed_by",
            "removal_reason",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "removed_at",
            "removed_by",
            "updated_at",
        ]


class AccessRequestSerializer(
    serializers.ModelSerializer
):
    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    volunteer_user_id = serializers.CharField(
        source="volunteer.user_id",
        read_only=True,
    )

    # Human-readable volunteer subject
    volunteer_subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    volunteer_email = serializers.EmailField(
        source="volunteer.email",
        read_only=True,
    )

    class Meta:
        model = VolunteerAccessRequest

        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "volunteer_user_id",
            "volunteer_subject",
            "volunteer_email",
            "status",
            "message",
            "requested_at",
            "decided_at",
            "decided_by",
            "decision_note",
        ]

        read_only_fields = [
            "id",
            "status",
            "requested_at",
            "decided_at",
            "decided_by",
        ]