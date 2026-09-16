from django.contrib import admin

from .models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "admin",
        "session_date",
        "started_at",
        "expires_at",
        "ended_at",
        "is_active",
    )

    list_filter = (
        "session_date",
        "is_active",
    )

    search_fields = (
        "admin__username",
    )

    readonly_fields = (
        "session_date",
        "started_at",
        "expires_at",
        "ended_at",
        "is_active",
    )


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "session",
        "student",
        "status",
        "marked_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "student__name",
        "student__roll_no",
    )

    readonly_fields = (
        "marked_at",
    )


@admin.register(VolunteerAttendance)
class VolunteerAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "session",
        "volunteer",
        "task",
        "status",
        "marked_at",
    )

    list_filter = (
        "task",
        "status",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
        "volunteer__email",
    )

    readonly_fields = (
        "marked_at",
    )