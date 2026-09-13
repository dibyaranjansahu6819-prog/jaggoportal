from django.db import transaction

from .models import StudentRegistrationSequence


def get_class_code(student_class):
    """
    Converts the class into the required roll-number code.

    LKG -> K1
    UKG -> K2
    1   -> 01
    9   -> 09
    10  -> 10
    """

    if student_class == "LKG":
        return "K1"

    if student_class == "UKG":
        return "K2"

    return student_class.zfill(2)


@transaction.atomic
def generate_student_roll_no(student_class):
    """
    Generates a globally sequential student roll number.

    Examples:

    Class 1 + priority 1
    -> JAA0101

    Class 9 + priority 35
    -> JAA0935

    LKG + priority 1
    -> JAAK101

    UKG + priority 2
    -> JAAK202
    """

    sequence, created = (
        StudentRegistrationSequence.objects
        .select_for_update()
        .get_or_create(
            pk=1,
            defaults={"value": 0}
        )
    )

    sequence.value += 1

    sequence.save(
        update_fields=["value"]
    )

    class_code = get_class_code(
        student_class
    )

    return (
        f"JAA"
        f"{class_code}"
        f"{sequence.value:02d}"
    )