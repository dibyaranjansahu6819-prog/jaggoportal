from rest_framework.permissions import BasePermission

from accounts.permissions import IsAdmin2


class Admin2OnlyPermission(IsAdmin2):
    """
    Allows access only to Admin 2 users.
    """

    pass