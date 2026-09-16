from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = "Send a real Gmail SMTP test email for Jaago Portal."

    def handle(self, *args, **options):

        sender = "abhyudayjaago@gmail.com"
        receiver = "dynaimorobotshooter12@gmail.com"

        subject = "Jaago Portal - Real Email Test"

        body = (
            "Hello,\n\n"
            "This is a real email test from the Jaago Portal backend.\n\n"
            "Sender: abhyudayjaago@gmail.com\n"
            "Receiver: dynaimorobotshooter12@gmail.com\n\n"
            "The Gmail SMTP configuration is working successfully.\n\n"
            "Regards, Jaago Team"
        )

        self.stdout.write(
            self.style.WARNING(
                "Attempting to send real email..."
            )
        )

        self.stdout.write(
            f"From: {sender}"
        )

        self.stdout.write(
            f"To: {receiver}"
        )

        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=sender,
                to=[receiver],
            )

            email.send(
                fail_silently=False
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "SUCCESS: Real email sent successfully!"
                )
            )

            self.stdout.write(
                f"Check inbox: {receiver}"
            )

        except Exception as exc:

            self.stdout.write(
                self.style.ERROR(
                    "FAILED: Email could not be sent."
                )
            )

            self.stdout.write(
                self.style.ERROR(
                    f"Error: {exc}"
                )
            )