from django.db.models.signals import post_save
from django.dispatch import receiver

from attendance.models import VolunteerAttendance

from .services import (
    check_and_create_caution,
    sync_attendance_xp,
)


@receiver(
    post_save,
    sender=VolunteerAttendance,
)
def volunteer_attendance_changed(
    sender,
    instance,
    created,
    **kwargs,
):
    sync_attendance_xp(instance)

    if (
        instance.attendance_source == "ASSIGNED"
        and instance.status == "ABSENT"
    ):
        check_and_create_caution(
            instance.volunteer
        )