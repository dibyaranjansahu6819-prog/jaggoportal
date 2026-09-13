import re

from django.db import transaction

from .models import RegistrationSequence


def get_last_name_code(full_name):
    """
    Converts the last name into a 3-character code.

    Dibyaranjan Sahu -> SAH
    Rahul Das        -> DAS
    Ankit Patra      -> PAT
    """

    parts = full_name.strip().split()

    if not parts:
        return "USR"

    last_name = parts[-1]

    # Keep English letters only
    last_name = re.sub(
        r"[^A-Za-z]",
        "",
        last_name
    ).upper()

    if not last_name:
        return "USR"

    # Make sure the code is exactly 3 characters
    return last_name[:3].ljust(3, "X")


def get_subject_code(subject):
    """
    Mathematics -> M
    English     -> E
    Odia        -> O
    """

    subject_name = subject.name.strip()

    if not subject_name:
        return "X"

    return subject_name[0].upper()


@transaction.atomic
def generate_teacher_user_id(name, subject):
    """
    Generates globally sequential IDs.

    Example:
    SAHM001
    SAHE002
    DASO003
    PATM004
    """

    sequence, created = (
        RegistrationSequence.objects
        .select_for_update()
        .get_or_create(
            pk=1,
            defaults={"value": 0}
        )
    )

    sequence.value += 1
    sequence.save(update_fields=["value"])

    last_name_code = get_last_name_code(name)
    subject_code = get_subject_code(subject)

    return (
        f"{last_name_code}"
        f"{subject_code}"
        f"{sequence.value:03d}"
    )