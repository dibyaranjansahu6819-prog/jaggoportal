import os
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Idempotently ensures a Django admin (superuser) account exists, using
    credentials from environment variables only (never hardcoded — this
    file is committed to source control). Safe to run on every deploy
    (e.g. chained into the Start Command) on hosts where a Shell/Pre-Deploy
    Command isn't available to run `createsuperuser` by hand.
    """

    help = "Create or update the Django admin superuser account from env vars."

    def handle(self, *args, **options):
        username = os.getenv("SUPERUSER_USERNAME")
        email = os.getenv("SUPERUSER_EMAIL", "")
        password = os.getenv("SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "SUPERUSER_USERNAME / SUPERUSER_PASSWORD not set — skipping."
                )
            )
            return

        user, _ = User.objects.get_or_create(username=username)
        user.email = email
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Ensured superuser account: {username}")
        )
