from django.contrib import admin

from .models import RegistrationSequence, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):

    list_display = (
        "user_id",
        "name",
        "course",
        "joining_year",
        "subject",
        "email",
    )

    search_fields = (
        "user_id",
        "name",
        "email",
        "whatsapp_number",
    )

    list_filter = (
        "course",
        "subject",
        "joining_year",
    )

    readonly_fields = (
        "user_id",
        "created_at",
    )


@admin.register(RegistrationSequence)
class RegistrationSequenceAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "value",
    )

    readonly_fields = (
        "value",
    )