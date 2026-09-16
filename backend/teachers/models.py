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