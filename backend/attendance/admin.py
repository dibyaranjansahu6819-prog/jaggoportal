from django.contrib import admin

from .models import (
    StudentAttendance,
    TeacherAttendance,
    Volunteer,
    VolunteerAssignment,
    PresentVolunteerAssignment,
)
from .models import AttendancePhoto


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "date",
        "status",
        "marked_at",
    )

    list_filter = (
        "date",
        "status",
    )

    search_fields = (
        "student__roll_no",
        "student__name",
    )


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "teacher",
        "date",
        "status",
        "marked_at",
    )

    list_filter = (
        "date",
        "status",
    )

    search_fields = (
        "teacher__user_id",
        "teacher__name",
    )


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone",
        "email",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "email",
    )

    list_filter = (
        "is_active",
    )


@admin.register(VolunteerAssignment)
class VolunteerAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "group",
        "volunteer",
        "assigned_at",
    )

    list_filter = (
        "group",
    )


@admin.register(PresentVolunteerAssignment)
class PresentVolunteerAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "volunteer",
        "date",
        "assigned_at",
    )

    list_filter = (
        "date",
    )

    search_fields = (
        "student__roll_no",
        "student__name",
        "volunteer__name",
    )
    
@admin.register(AttendancePhoto)
class AttendancePhotoAdmin(
    admin.ModelAdmin
):

    list_display = (
        "id",
        "photo_type",
        "date",
        "uploaded_at",
    )

    list_filter = (
        "photo_type",
        "date",
    )

    readonly_fields = (
        "uploaded_at",
    )