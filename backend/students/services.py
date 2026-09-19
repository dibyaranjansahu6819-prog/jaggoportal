from django.db import transaction
from django.db.models import Sum

from .models import StudentXPTransaction


STUDENT_HOMEWORK_COMPLETED_XP = 10


def get_student_xp(student):
    """
    Return the student's total XP.
    """

    total = (
        StudentXPTransaction.objects
        .filter(student=student)
        .aggregate(total=Sum("points"))
        ["total"]
    )

    return total or 0


@transaction.atomic
def sync_homework_xp(homework):
    """
    Automatically synchronize XP for one homework record.

    Rules:
    - COMPLETED -> +10 XP
    - PENDING   -> 0 XP
    - One homework can generate only one XP transaction.
    """

    # Remove an existing automatic transaction for this homework.
    # This keeps the operation idempotent.
    StudentXPTransaction.objects.filter(
        homework=homework,
        source="HOMEWORK_COMPLETED",
    ).delete()

    # Pending homework gives no XP.
    if homework.status != "COMPLETED":
        return None

    # Completed homework automatically gives +10 XP.
    xp_transaction = StudentXPTransaction.objects.create(
        student=homework.student,
        points=STUDENT_HOMEWORK_COMPLETED_XP,
        source="HOMEWORK_COMPLETED",
        reason="Homework completed",
        homework=homework,
        created_by=None,
    )

    return xp_transaction