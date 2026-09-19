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

    GROUP_CHOICES = [
        ("ClassA", "Class A"),
        ("ClassB", "Class B"),
        ("ClassC", "Class C"),
        ("ClassD", "Class D"),
        ("ClassE", "Class E"),
    ]

    roll_no = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    name = models.CharField(
        max_length=150,
    )

    student_class = models.CharField(
        max_length=3,
        choices=CLASS_CHOICES,
    )

    group = models.CharField(
        max_length=20,
        choices=GROUP_CHOICES,
        editable=False,
    )

    school_name = models.CharField(
        max_length=200,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def get_group_for_class(self):
        if self.student_class in ["LKG", "UKG"]:
            return "ClassE"

        if self.student_class in ["1", "2", "3"]:
            return "ClassA"

        if self.student_class in ["4", "5", "6"]:
            return "ClassB"

        if self.student_class in ["7", "8"]:
            return "ClassC"

        if self.student_class in ["9", "10"]:
            return "ClassD"

        return None

    def save(self, *args, **kwargs):
        self.group = self.get_group_for_class()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.roll_no} - "
            f"{self.name} - "
            f"{self.student_class} - "
            f"{self.group}"
        )


class StudentHomework(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="homework_records",
    )

    assignment = models.ForeignKey(
        "admin2.VolunteerAssignment",
        on_delete=models.PROTECT,
        related_name="student_homework_records",
    )

    work_session = models.ForeignKey(
        "teachers.VolunteerWorkSession",
        on_delete=models.PROTECT,
        related_name="student_homework_records",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "assignment"],
                name="unique_student_homework_per_assignment",
            ),
        ]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.assignment.assignment_date} - "
            f"{self.status}"
        )
        
class StudentXPTransaction(models.Model):
    SOURCE_CHOICES = [
        ("HOMEWORK_COMPLETED", "Homework Completed"),
    ]

    student = models.ForeignKey(
        Student,
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

    homework = models.OneToOneField(
        "students.StudentHomework",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="xp_transaction",
    )

    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="student_xp_changes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.points} XP - "
            f"{self.source}"
        )