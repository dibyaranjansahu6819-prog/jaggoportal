from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """
    Allows access only to logged-in users.
    """

    message = "Authentication is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
        )


class IsAdmin1(BasePermission):
    """
    Allows access only to Admin 1.
    """

    message = "Admin 1 permission is required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        profile = getattr(request.user, "profile", None)

        return bool(
            profile
            and profile.is_active
            and profile.role == "ADMIN1"
        )


class IsAdmin2(BasePermission):
    """
    Allows access only to Admin 2.
    """

    message = "Admin 2 permission is required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        profile = getattr(request.user, "profile", None)

        return bool(
            profile
            and profile.is_active
            and profile.role == "ADMIN2"
        )


class IsAdmin(BasePermission):
    """
    Allows access to Admin 1 or Admin 2.
    """

    message = "Administrator permission is required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        profile = getattr(request.user, "profile", None)

        return bool(
            profile
            and profile.is_active
            and profile.role in [
                "ADMIN1",
                "ADMIN2",
            ]
        )


class IsTeacherVolunteer(BasePermission):
    """
    Allows access only to Teacher / Volunteer users.
    """

    message = "Teacher / Volunteer permission is required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        profile = getattr(request.user, "profile", None)

        return bool(
            profile
            and profile.is_active
            and profile.role == "TEACHER_VOLUNTEER"
        )


class IsStudent(BasePermission):
    """
    Allows access only to Student users.
    """

    message = "Student permission is required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        profile = getattr(request.user, "profile", None)

        return bool(
            profile
            and profile.is_active
            and profile.role == "STUDENT"
        )