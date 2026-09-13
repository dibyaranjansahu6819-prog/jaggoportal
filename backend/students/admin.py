from django.contrib import admin

from .models import (
    Student,
    StudentRegistrationSequence,
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "roll_no",
        "name",
        "student_class",
        "school_name",
        "created_at",
    )

    search_fields = (
        "roll_no",
        "name",
        "school_name",
    )

    list_filter = (
        "student_class",
        "school_name",
    )

    readonly_fields = (
        "roll_no",
        "created_at",
    )


@admin.register(StudentRegistrationSequence)
class StudentRegistrationSequenceAdmin(
    admin.ModelAdmin
):

    list_display = (
        "id",
        "value",
    )

    readonly_fields = (
        "value",
    )