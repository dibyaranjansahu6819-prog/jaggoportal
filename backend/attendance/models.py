from django.db import models
from django.utils import timezone

from students.models import Student
from teachers.models import Teacher


class AttendanceSession(models.Model):
    """
    Attendance session controlled by Admin1.

    The date is automatically determined by the backend.
    Admin1 cannot select or change the date.
    """

    admin = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="attendance_sessions",
    )

    session_date = models.DateField(
        default=timezone.localdate,
        editable=False,
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField()

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return (
            f"Attendance - "
            f"{self.session_date} - "
            f"{self.admin.username}"
        )

    @property
    def has_expired(self):
        return timezone.now() >= self.expires_at

    def close_if_expired(self):
        if self.is_active and self.has_expired:
            self.is_active = False

            if self.ended_at is None:
                self.ended_at = timezone.now()

            self.save(
                update_fields=[
                    "is_active",
                    "ended_at",
                ]
            )

        return not self.is_active


class StudentAttendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="student_attendance",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ABSENT",
    )

    marked_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student"],
                name="unique_student_attendance_per_session",
            ),
        ]

        ordering = [
            "student__student_class",
            "student__roll_no",
        ]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.student.name} - "
            f"{self.status}"
        )


class VolunteerAttendance(models.Model):
    TASK_CHOICES = [
        ("TEACHING", "Teaching"),
        ("CHECKING", "Checking"),
    ]

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    SOURCE_CHOICES = [
        ("ASSIGNED", "Assigned"),
        ("SPECIAL_ADDED", "Special Added"),
    ]

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="volunteer_attendance",
    )

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="volunteer_attendance_records",
    )

    task = models.CharField(
        max_length=20,
        choices=TASK_CHOICES,
    )

    attendance_source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="ASSIGNED",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ABSENT",
    )

    marked_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "session",
                    "volunteer",
                ],
                name="unique_volunteer_attendance_per_session",
            )
        ]

        ordering = [
            "volunteer__name",
        ]

    def __str__(self):
        return (
            f"{self.volunteer.user_id} - "
            f"{self.task} - "
            f"{self.status}"
        )