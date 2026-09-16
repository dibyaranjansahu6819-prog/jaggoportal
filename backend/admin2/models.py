from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from teachers.models import Teacher


class VolunteerAssignment(models.Model):
    CLASS_CHOICES = [
        ("ClassA", "Class A"),
        ("ClassB", "Class B"),
        ("ClassC", "Class C"),
        ("ClassD", "Class D"),
    ]

    TASK_CHOICES = [
        ("TEACHING", "Teaching"),
        ("CHECKING", "Checking"),
    ]

    EMAIL_STATUS_CHOICES = [
        ("NOT_SENT", "Not Sent"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
    ]

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="admin2_assignments",
    )

    assignment_date = models.DateField(
        default=timezone.localdate,
        db_index=True,
    )

    assigned_class = models.CharField(
        max_length=20,
        choices=CLASS_CHOICES,
    )

    task = models.CharField(
        max_length=20,
        choices=TASK_CHOICES,
    )

    instruction = models.TextField(
        blank=True,
        default="",
    )

    attachment = models.FileField(
        upload_to="admin2/assignments/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    sender_email = models.EmailField(
        blank=True,
        default="",
    )

    email_status = models.CharField(
        max_length=20,
        choices=EMAIL_STATUS_CHOICES,
        default="NOT_SENT",
    )

    email_sent_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    email_error = models.TextField(
        blank=True,
        default="",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_admin2_assignments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-assignment_date",
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=["assignment_date"]
            ),
            models.Index(
                fields=[
                    "volunteer",
                    "assignment_date",
                ]
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["volunteer", "assignment_date"],
                name="unique_volunteer_assignment_per_day",
            ),
        ]

    def clean(self):
        if not self.volunteer_id:
            raise ValidationError(
                {
                    "volunteer":
                        "Registered volunteer is required."
                }
            )

        if not self.volunteer.email:
            raise ValidationError(
                {
                    "volunteer":
                        "Volunteer has no registered email."
                }
            )

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.assignment_date} - "
            f"{self.assigned_class} - "
            f"{self.task}"
        )


class VolunteerXPTransaction(models.Model):
    SOURCE_CHOICES = [
        ("ATTENDANCE_PRESENT", "Attendance Present"),
        ("ATTENDANCE_ABSENT", "Attendance Absent"),
        ("SPECIAL_PRESENT", "Special Added Present"),
        ("ADMIN_INCREASE", "Admin Increase"),
        ("ADMIN_DECREASE", "Admin Decrease"),
    ]

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="xp_transactions",
    )

    points = models.IntegerField()

    source = models.CharField(
        max_length=30,
        choices=SOURCE_CHOICES,
    )

    reason = models.TextField(
        blank=True,
        default="",
    )

    attendance = models.OneToOneField(
        "attendance.VolunteerAttendance",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="xp_transaction",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="admin2_xp_changes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.points} XP - "
            f"{self.source}"
        )


class VolunteerCaution(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("RESOLVED", "Resolved"),
    ]

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="cautions",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    absence_streak = models.PositiveIntegerField(
        default=3,
    )

    caution_date = models.DateField(
        default=timezone.localdate,
    )

    email_sent = models.BooleanField(
        default=False,
    )

    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    note = models.TextField(
        blank=True,
        default="",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resolved_volunteer_cautions",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["volunteer", "status"]
            ),
            models.Index(
                fields=["status"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.status}"
        )


class VolunteerAccountStatus(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("CAUTION", "Caution"),
        ("REMOVED", "Removed"),
    ]

    volunteer = models.OneToOneField(
        Teacher,
        on_delete=models.PROTECT,
        related_name="admin2_status",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    removed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="removed_volunteers",
    )

    removal_reason = models.TextField(
        blank=True,
        default="",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.status}"
        )


class VolunteerAccessRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DENIED", "Denied"),
    ]

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="access_requests",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    message = models.TextField(
        blank=True,
        default="",
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    decided_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decided_volunteer_access_requests",
    )

    decision_note = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        ordering = ["-requested_at"]

        indexes = [
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["volunteer", "status"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.status}"
        )