from django.contrib import admin

from .models import (
    DailySchoolStatus,
    VolunteerAccountStatus,
    VolunteerAccessRequest,
    VolunteerAssignment,
    VolunteerCaution,
    VolunteerXPTransaction,
)


@admin.register(DailySchoolStatus)
class DailySchoolStatusAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "status",
        "playing_day_email_status",
        "playing_day_email_sent_at",
        "created_by",
    )
    list_filter = (
        "status",
        "playing_day_email_status",
        "date",
    )
    search_fields = ("date",)


@admin.register(VolunteerAssignment)
class VolunteerAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "volunteer",
        "assignment_date",
        "assigned_class",
        "task",
        "email_status",
        "email_sent_at",
    )

    list_filter = (
        "assignment_date",
        "assigned_class",
        "task",
        "email_status",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
        "volunteer__email",
    )


@admin.register(VolunteerXPTransaction)
class VolunteerXPTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer",
        "points",
        "source",
        "created_by",
        "created_at",
    )

    list_filter = (
        "source",
        "created_at",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
        "reason",
    )


@admin.register(VolunteerCaution)
class VolunteerCautionAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer",
        "status",
        "absence_streak",
        "caution_date",
        "email_sent",
    )

    list_filter = (
        "status",
        "email_sent",
        "caution_date",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
    )


@admin.register(VolunteerAccountStatus)
class VolunteerAccountStatusAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer",
        "status",
        "removed_at",
        "updated_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
        "volunteer__email",
    )


@admin.register(VolunteerAccessRequest)
class VolunteerAccessRequestAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer",
        "status",
        "requested_at",
        "decided_at",
        "decided_by",
    )

    list_filter = (
        "status",
        "requested_at",
    )

    search_fields = (
        "volunteer__name",
        "volunteer__user_id",
        "volunteer__email",
        "message",
    )