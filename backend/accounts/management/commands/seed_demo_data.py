import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from courses.models import Course, Subject
from accounts.demo import _demo_volunteer


class Command(BaseCommand):
    help = "Seeds initial demo data (Courses, Subjects, Admin accounts, and Demo Volunteer)."

    def handle(self, *args, **options):
        # 1. Seed Courses
        courses = ["Primary School", "Middle School", "High School"]
        for c in courses:
            Course.objects.get_or_create(name=c)
        self.stdout.write(self.style.SUCCESS("Ensured Courses"))

        # 2. Seed Subjects
        subjects = ["Mathematics", "Science", "English", "Social Studies", "Hindi"]
        for s in subjects:
            Subject.objects.get_or_create(name=s)
        self.stdout.write(self.style.SUCCESS("Ensured Subjects"))

        # 3. Seed Admins
        accounts = [
            (
                os.getenv("ADMIN1_USERNAME", "admin1"),
                os.getenv("ADMIN1_PASSWORD", "admin123"),
                "ADMIN1",
            ),
            (
                os.getenv("ADMIN2_USERNAME", "admin2"),
                os.getenv("ADMIN2_PASSWORD", "admin123"),
                "ADMIN2",
            ),
        ]

        for username, password, role in accounts:
            user, _ = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.is_active = True
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role, "is_active": True},
            )
            self.stdout.write(self.style.SUCCESS(f"Ensured {role} account: {username}"))

        # 4. Seed Demo Volunteer
        try:
            _, teacher = _demo_volunteer()
            self.stdout.write(self.style.SUCCESS(f"Ensured Demo Volunteer: {teacher.user_id}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not seed demo volunteer: {e}"))

        self.stdout.write(self.style.SUCCESS("All seed demo data ready!"))
