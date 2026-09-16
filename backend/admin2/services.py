from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from attendance.models import VolunteerAttendance

from .models import (
    VolunteerAccountStatus,
    VolunteerAssignment,
    VolunteerCaution,
    VolunteerXPTransaction,
)


# ============================================================
# XP CONSTANTS
# ============================================================

NORMAL_PRESENT_XP = 10
NORMAL_ABSENT_XP = -10
SPECIAL_PRESENT_XP = 15


# ============================================================
# VOLUNTEER XP
# ============================================================

def get_volunteer_xp(volunteer):
    """
    Return the current total XP of a volunteer.
    """

    return sum(
        VolunteerXPTransaction.objects.filter(
            volunteer=volunteer
        ).values_list(
            "points",
            flat=True,
        )
    )


# ============================================================
# VOLUNTEER ACCOUNT STATUS
# ============================================================

def get_current_status(volunteer):
    """
    Get the current account status.

    If a status record does not exist yet,
    create an ACTIVE status automatically.
    """

    status, _ = VolunteerAccountStatus.objects.get_or_create(
        volunteer=volunteer,
        defaults={
            "status": "ACTIVE",
        },
    )

    return status


# ============================================================
# ATTENDANCE XP SYNCHRONIZATION
# ============================================================

@transaction.atomic
def sync_attendance_xp(attendance):
    """
    Synchronize the automatic XP transaction for one
    volunteer attendance record.

    Rules:

    ASSIGNED:
        PRESENT = +10 XP
        ABSENT  = -10 XP

    SPECIAL_ADDED:
        PRESENT = +15 XP
        ABSENT  = 0 XP
    """

    volunteer = attendance.volunteer

    # --------------------------------------------------------
    # Remove previous automatic XP transaction
    # --------------------------------------------------------

    existing = VolunteerXPTransaction.objects.filter(
        attendance=attendance
    ).first()

    if existing:
        existing.delete()

    # --------------------------------------------------------
    # Calculate new XP
    # --------------------------------------------------------

    points = 0
    source = None
    reason = ""

    # --------------------------------------------------------
    # SPECIAL ADDED VOLUNTEER
    # --------------------------------------------------------

    if attendance.attendance_source == "SPECIAL_ADDED":

        if attendance.status == "PRESENT":
            points = SPECIAL_PRESENT_XP

            source = "SPECIAL_PRESENT"

            reason = (
                "Volunteer was manually added by Admin 1 "
                "and marked present."
            )

        else:
            # Special-added absent = 0 XP
            points = 0

    # --------------------------------------------------------
    # NORMAL ASSIGNED VOLUNTEER
    # --------------------------------------------------------

    else:

        if attendance.status == "PRESENT":
            points = NORMAL_PRESENT_XP

            source = "ATTENDANCE_PRESENT"

            reason = (
                "Assigned volunteer marked present."
            )

        else:
            points = NORMAL_ABSENT_XP

            source = "ATTENDANCE_ABSENT"

            reason = (
                "Assigned volunteer marked absent."
            )

    # --------------------------------------------------------
    # No transaction for zero XP
    # --------------------------------------------------------

    if points == 0:
        return None

    # --------------------------------------------------------
    # Create automatic XP transaction
    # --------------------------------------------------------

    return VolunteerXPTransaction.objects.create(
        volunteer=volunteer,
        points=points,
        source=source,
        reason=reason,
        attendance=attendance,
    )


# ============================================================
# ASSIGNED ABSENCE STREAK
# ============================================================

def get_assigned_absence_streak(volunteer):
    """
    Calculate the current consecutive assigned-absence streak.

    Rules:

    1. Only SENT assignments count.
    2. Days without an assignment are ignored.
    3. Multiple assignments on the same date count as ONE day.
    4. The latest assigned date is checked first.
    5. If the latest assigned attendance is ABSENT,
       continue backwards through assigned dates.
    6. If an assigned date has PRESENT attendance,
       the streak stops.
    7. If attendance is missing for an assigned date,
       that date is ignored because no attendance result
       has been recorded yet.
    """

    # --------------------------------------------------------
    # Get all sent assignments.
    # --------------------------------------------------------

    assignments = (
        VolunteerAssignment.objects.filter(
            volunteer=volunteer,
            email_status="SENT",
        )
        .order_by("-assignment_date", "-created_at")
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # A volunteer can currently have multiple assignment
    # records on the same date.
    #
    # Attendance is counted by DATE, not by assignment row.
    #
    # Example:
    #
    # Monday:
    #   Teaching
    #   Checking
    #
    # This must count as ONE assigned day.
    # --------------------------------------------------------

    unique_dates = []
    seen_dates = set()

    for assignment in assignments:

        assignment_date = assignment.assignment_date

        if assignment_date in seen_dates:
            continue

        seen_dates.add(assignment_date)
        unique_dates.append(assignment_date)

    # --------------------------------------------------------
    # Calculate streak
    # --------------------------------------------------------

    streak = 0

    for assignment_date in unique_dates:

        attendance = (
            VolunteerAttendance.objects.filter(
                volunteer=volunteer,
                session__session_date=assignment_date,
                attendance_source="ASSIGNED",
            )
            .order_by("-marked_at")
            .first()
        )

        # ----------------------------------------------------
        # No attendance recorded yet.
        #
        # Do not count it as absent and do not break the
        # streak. This allows the attendance session to be
        # completed later.
        # ----------------------------------------------------

        if not attendance:
            continue

        # ----------------------------------------------------
        # ABSENT
        # ----------------------------------------------------

        if attendance.status == "ABSENT":
            streak += 1
            continue

        # ----------------------------------------------------
        # PRESENT
        #
        # Consecutive absence streak ends here.
        # ----------------------------------------------------

        break

    return streak


# ============================================================
# CAUTION EMAIL
# ============================================================

def send_caution_email(caution):
    """
    Send the caution email to the volunteer.

    The email is sent only to the volunteer's
    registered email address.
    """

    volunteer = caution.volunteer

    if not volunteer.email:
        return False

    subject = (
        "Jaago Team - Attendance Caution"
    )

    body = (
        f"Hello {volunteer.name},\n\n"
        "Our attendance records show that you have been "
        "absent for three consecutive assigned sessions.\n\n"
        "Please contact the Jaago Team if there is a "
        "reason for your absence.\n\n"
        "Regards, Jaago Team"
    )

    try:

        email = EmailMessage(
            subject=subject,
            body=body,
            to=[
                volunteer.email
            ],
        )

        email.send(
            fail_silently=False
        )

        caution.email_sent = True
        caution.email_sent_at = timezone.now()

        caution.save(
            update_fields=[
                "email_sent",
                "email_sent_at",
                "updated_at",
            ]
        )

        return True

    except Exception:
        return False


# ============================================================
# CREATE CAUTION
# ============================================================

@transaction.atomic
def check_and_create_caution(volunteer):
    """
    Check the volunteer's absence streak.

    If the volunteer has three or more consecutive
    assigned absences:

    1. Create an ACTIVE caution.
    2. Change account status to CAUTION.
    3. Send caution email.

    Existing active caution is not duplicated.
    """

    streak = get_assigned_absence_streak(
        volunteer
    )

    # --------------------------------------------------------
    # Less than three consecutive absences
    # --------------------------------------------------------

    if streak < 3:
        return None

    # --------------------------------------------------------
    # Do not create duplicate active cautions
    # --------------------------------------------------------

    existing = VolunteerCaution.objects.filter(
        volunteer=volunteer,
        status="ACTIVE",
    ).first()

    if existing:

        # Keep the streak value updated.
        if existing.absence_streak != streak:

            existing.absence_streak = streak

            existing.save(
                update_fields=[
                    "absence_streak",
                    "updated_at",
                ]
            )

        return existing

    # --------------------------------------------------------
    # Create caution
    # --------------------------------------------------------

    caution = VolunteerCaution.objects.create(
        volunteer=volunteer,
        status="ACTIVE",
        absence_streak=streak,
        caution_date=timezone.localdate(),
    )

    # --------------------------------------------------------
    # Update volunteer account status
    # --------------------------------------------------------

    account_status = get_current_status(
        volunteer
    )

    # Never overwrite REMOVED status automatically.
    #
    # If Admin 2 has already removed the volunteer,
    # caution should not reactivate/change that account.
    if account_status.status == "ACTIVE":

        account_status.status = "CAUTION"

        account_status.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    # --------------------------------------------------------
    # Send caution email
    # --------------------------------------------------------

    send_caution_email(
        caution
    )

    return caution