import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import UserProfile


class Command(BaseCommand):
    """
    Idempotently ensures the Admin 1 and Admin 2 accounts exist with the
    configured username/password. Safe to run on every deploy (e.g. chained
    into the Start Command) on hosts where a Shell/Pre-Deploy Command isn't
    available to run this by hand.
    """

    help = "Create or update the Admin 1 and Admin 2 accounts from env vars."

    def handle(self, *args, **options):
        accounts = [
            (
                os.getenv("ADMIN1_USERNAME"),
                os.getenv("ADMIN1_PASSWORD"),
                "ADMIN1",
            ),
            (
                os.getenv("ADMIN2_USERNAME"),
                os.getenv("ADMIN2_PASSWORD"),
                "ADMIN2",
            ),
        ]

        for username, password, role in accounts:
            if not username or not password:
                self.stdout.write(
                    self.style.WARNING(
                        f"{role}_USERNAME / {role}_PASSWORD not set — skipping."
                    )
                )
                continue

            user, _ = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.is_active = True
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role, "is_active": True},
            )

            self.stdout.write(
                self.style.SUCCESS(f"Ensured {role} account: {username}")
            )
