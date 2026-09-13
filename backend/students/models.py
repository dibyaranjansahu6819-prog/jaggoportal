from django.db import models


class StudentRegistrationSequence(models.Model):
    value = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Student Registration Sequence"
        verbose_name_plural = "Student Registration Sequence"

    def __str__(self):
        return str(self.value)


class Student(models.Model):

    CLASS_CHOICES = [
        ("LKG", "LKG"),
        ("UKG", "UKG"),
        ("1", "Class 1"),
        ("2", "Class 2"),
        ("3", "Class 3"),
        ("4", "Class 4"),
        ("5", "Class 5"),
        ("6", "Class 6"),
        ("7", "Class 7"),
        ("8", "Class 8"),
        ("9", "Class 9"),
        ("10", "Class 10"),
    ]

    roll_no = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    name = models.CharField(
        max_length=150
    )

    student_class = models.CharField(
        max_length=3,
        choices=CLASS_CHOICES
    )

    school_name = models.CharField(
        max_length=200
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.roll_no} - {self.name}"