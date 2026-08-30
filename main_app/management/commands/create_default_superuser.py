import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a default superuser if one doesn't already exist, using env vars."

    def handle(self, *args, **options):
        User = get_user_model()

        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stderr.write(self.style.ERROR(
                "DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD "
                "must be set as environment variables."
            ))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f"Superuser with email {email} already exists. Skipping."
            ))
            return

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f"Superuser {email} created successfully."
        ))