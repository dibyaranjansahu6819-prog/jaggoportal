from django.contrib.auth.models import User
from django.db import models

from courses.models import Course, Subject


class RegistrationSequence(models.Model):
    value = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Registration Sequence"
        verbose_name_plural = "Registration Sequence"

    def __str__(self):
        return str(self.value)


class Teacher(models.Model):

    FREE_DAY_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
    ]

    # Django authentication account
    auth_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        null=True,
        blank=True,
    )

    # Automatically generated Teacher ID
    user_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    name = models.CharField(
        max_length=150
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="teachers",
    )

    joining_year = models.PositiveIntegerField()

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="teachers",
    )

    email = models.EmailField(
        unique=True
    )

    whatsapp_number = models.CharField(
        max_length=15
    )

    free_days = models.JSONField(
        default=list
    )

    # Kept temporarily for compatibility with
    # the existing Teacher records.
    #
    # New authentication uses Django's User model.
    password = models.CharField(
        max_length=128
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user_id} - {self.name}"

class VolunteerWorkSession(models.Model):
    """
    Tracks the actual working session of a volunteer for an assignment.

    A volunteer can have one work session for a particular assignment.
    ForeignKey is intentionally used instead of OneToOneField so that
    a future authorized substitute volunteer can work on another
    volunteer's assignment.
    """

    STATUS_CHOICES = [
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]

    assignment = models.ForeignKey(
        "admin2.VolunteerAssignment",
        on_delete=models.PROTECT,
        related_name="work_sessions",
    )

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="work_sessions",
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    total_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="NOT_STARTED",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "volunteer"],
                name="unique_volunteer_work_session_per_assignment",
            )
        ]

    def __str__(self):
        return (
            f"{self.volunteer.name} - "
            f"{self.assignment.assignment_date} - "
            f"{self.status}"
        )
        
class StudentProgress(models.Model):
    """
    Stores a volunteer's progress record for a student.

    Progress can only be submitted after the volunteer completes
    the assigned work session.
    """

    PERFORMANCE_CHOICES = [
        ("POOR", "Poor"),
        ("AVERAGE", "Average"),
        ("GOOD", "Good"),
    ]

    assignment = models.ForeignKey(
        "admin2.VolunteerAssignment",
        on_delete=models.PROTECT,
        related_name="student_progress_records",
    )

    work_session = models.ForeignKey(
        "teachers.VolunteerWorkSession",
        on_delete=models.PROTECT,
        related_name="student_progress_records",
    )

    volunteer = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="student_progress_records",
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="volunteer_progress_records",
    )

    performance = models.CharField(
        max_length=20,
        choices=PERFORMANCE_CHOICES,
    )

    feedback = models.TextField(
        blank=True,
        default="",
    )

    homework_given = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-updated_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assignment",
                    "volunteer",
                    "student",
                ],
                name="unique_student_progress_per_assignment",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.volunteer.user_id} - "
            f"{self.performance}"
        )