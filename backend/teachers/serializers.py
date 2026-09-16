from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction

from rest_framework import serializers

from .models import Teacher
from .utils import generate_teacher_user_id

from accounts.utils import ensure_teacher_volunteer_profile


class TeacherRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    confirm_password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = Teacher

        fields = [
            "id",
            "user_id",
            "name",
            "course",
            "joining_year",
            "subject",
            "email",
            "whatsapp_number",
            "free_days",
            "password",
            "confirm_password",
        ]

        read_only_fields = [
            "id",
            "user_id",
        ]

    def validate_email(self, value):

        value = value.strip().lower()

        if Teacher.objects.filter(
            email=value
        ).exists():

            raise serializers.ValidationError(
                "A teacher with this email already exists."
            )

        if User.objects.filter(
            username=value
        ).exists():

            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_whatsapp_number(self, value):

        value = value.strip()

        if not value.isdigit():

            raise serializers.ValidationError(
                "WhatsApp number must contain only digits."
            )

        if len(value) != 10:

            raise serializers.ValidationError(
                "WhatsApp number must be exactly 10 digits."
            )

        return value

    def validate_joining_year(self, value):

        if value < 1900 or value > 2100:

            raise serializers.ValidationError(
                "Please enter a valid joining year."
            )

        return value

    def validate_free_days(self, value):

        if not isinstance(value, list):

            raise serializers.ValidationError(
                "Free days must be a list."
            )

        if len(value) == 0:

            raise serializers.ValidationError(
                "Please select at least one free day."
            )

        valid_days = {
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        }

        invalid_days = set(value) - valid_days

        if invalid_days:

            raise serializers.ValidationError(
                "Invalid free day(s): "
                + ", ".join(sorted(invalid_days))
            )

        if len(value) != len(set(value)):

            raise serializers.ValidationError(
                "Free days cannot be duplicated."
            )

        return value

    def validate(self, data):

        if data["password"] != data["confirm_password"]:

            raise serializers.ValidationError({
                "confirm_password":
                    "Passwords do not match."
            })

        return data

    @transaction.atomic
    def create(self, validated_data):

        validated_data.pop("confirm_password")

        password = validated_data.pop("password")

        name = validated_data["name"]
        subject = validated_data["subject"]
        email = validated_data["email"]

        # Generate the unique teacher ID.
        #
        # Example:
        # Dibyaranjan Sahu + Mathematics
        # -> SAHM001
        user_id = generate_teacher_user_id(
            name,
            subject
        )

        # Create Django authentication account.
        #
        # We keep email as the username so the existing
        # teacher login system continues to work.
        auth_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )

        # Connect the Django authentication account
        # with the Teacher profile.
        validated_data["auth_user"] = auth_user

        # Store generated Teacher ID.
        validated_data["user_id"] = user_id

        # Keep the hashed password in the existing
        # Teacher model for backward compatibility.
        validated_data["password"] = make_password(
            password
        )

        # Create the Teacher / Volunteer role profile.
        #
        # Teacher and Volunteer are the SAME account role
        # in Jaago Portal.
        ensure_teacher_volunteer_profile(
            auth_user
        )

        return Teacher.objects.create(
            **validated_data
        )