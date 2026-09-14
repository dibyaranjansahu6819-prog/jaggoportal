from django.db import models

from students.models import Student
from teachers.models import Teacher


# ============================================================
# STUDENT ATTENDANCE
# ============================================================

class StudentAttendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ABSENT",
    )

    marked_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_per_day",
            )
        ]
        ordering = ["student__roll_no"]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.date} - "
            f"{self.status}"
        )


# ============================================================
# TEACHER ATTENDANCE
# ============================================================

class TeacherAttendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ABSENT",
    )

    marked_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "date"],
                name="unique_teacher_attendance_per_day",
            )
        ]
        ordering = ["teacher__user_id"]

    def __str__(self):
        return (
            f"{self.teacher.user_id} - "
            f"{self.date} - "
            f"{self.status}"
        )


# ============================================================
# VOLUNTEER
# ============================================================

class Volunteer(models.Model):

    name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# ============================================================
# PERMANENT VOLUNTEER ASSIGNMENT
# ============================================================

class VolunteerAssignment(models.Model):

    GROUP_CHOICES = [
        ("LKG_UKG", "LKG - UKG"),
        ("CLASS_1_3", "Class 1 - 3"),
        ("CLASS_4_6", "Class 4 - 6"),
        ("CLASS_7_8", "Class 7 - 8"),
        ("CLASS_9_10", "Class 9 - 10"),
    ]

    volunteer = models.ForeignKey(
        Volunteer,
        on_delete=models.PROTECT,
        related_name="assigned_groups"
    )

    group = models.CharField(
        max_length=20,
        choices=GROUP_CHOICES,
        unique=True
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.get_group_display()} - "
            f"{self.volunteer.name}"
        )


# ============================================================
# PRESENT VOLUNTEER FOR A STUDENT
# ============================================================

class PresentVolunteerAssignment(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="present_volunteer_assignments"
    )

    volunteer = models.ForeignKey(
        Volunteer,
        on_delete=models.PROTECT,
        related_name="present_student_assignments"
    )

    date = models.DateField()

    assigned_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_present_volunteer_per_student_day"
            )
        ]

    def __str__(self):
        return (
            f"{self.student.roll_no} - "
            f"{self.volunteer.name} - "
            f"{self.date}"
        )


# ============================================================
# DAILY VOLUNTEER ATTENDANCE
# ============================================================

class VolunteerDailyAttendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    volunteer = models.ForeignKey(
        Volunteer,
        on_delete=models.PROTECT,
        related_name="daily_attendance"
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PRESENT"
    )

    marked_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["volunteer", "date"],
                name="unique_volunteer_attendance_per_day"
            )
        ]

        ordering = [
            "volunteer__name"
        ]

    def __str__(self):
        return (
            f"{self.volunteer.name} - "
            f"{self.date} - "
            f"{self.status}"
        )


# ============================================================
# ATTENDANCE SESSION PHOTO
# ============================================================

class AttendancePhoto(models.Model):

    PHOTO_TYPE_CHOICES = [
        ("STUDENT", "Student Attendance"),
        ("VOLUNTEER", "Volunteer Attendance"),
    ]

    photo = models.ImageField(
        upload_to="attendance_photos/"
    )

    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES
    )

    date = models.DateField()

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.get_photo_type_display()} - "
            f"{self.date}"
        )
