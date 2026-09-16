from django.db import transaction

from .models import StudentRegistrationSequence


def get_class_code(student_class):
    if student_class == "LKG":
        return "K1"

    if student_class == "UKG":
        return "K2"

    return student_class.zfill(2)


@transaction.atomic
def generate_student_roll_no(student_class):
    sequence, created = (
        StudentRegistrationSequence.objects
        .select_for_update()
        .get_or_create(
            pk=1,
            defaults={"value": 0},
        )
    )

    sequence.value += 1
    sequence.save(update_fields=["value"])

    class_code = get_class_code(student_class)

    return f"JAA{class_code}{sequence.value:02d}"