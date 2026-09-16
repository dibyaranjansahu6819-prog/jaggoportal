from django.contrib.auth.models import User

from .models import UserProfile


def get_user_profile(user):
    """
    Safely return the UserProfile for a Django user.
    """
    if not user or not user.is_authenticated:
        return None

    return UserProfile.objects.filter(
        user=user,
        is_active=True,
    ).first()


def get_user_role(user):
    """
    Return the active role of a user.
    """
    profile = get_user_profile(user)

    if not profile:
        return None

    return profile.role


def create_or_update_user_profile(
    user,
    role,
):
    """
    Create a profile if it doesn't exist.

    If it already exists, update its role.
    """
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": role,
            "is_active": True,
        },
    )

    if not created:
        profile.role = role
        profile.is_active = True
        profile.save(
            update_fields=[
                "role",
                "is_active",
                "updated_at",
            ]
        )

    return profile


def ensure_teacher_volunteer_profile(user):
    """
    Make sure a teacher/volunteer Django user has the
    correct role profile.
    """
    return create_or_update_user_profile(
        user=user,
        role="TEACHER_VOLUNTEER",
    )


def ensure_student_profile(user):
    """
    Make sure a student Django user has the
    correct role profile.
    """
    return create_or_update_user_profile(
        user=user,
        role="STUDENT",
    )