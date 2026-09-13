from rest_framework import serializers

from .models import Student
from .utils import generate_student_roll_no


class StudentRegistrationSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Student

        fields = [
            "id",
            "roll_no",
            "name",
            "student_class",
            "school_name",
        ]

        read_only_fields = [
            "id",
            "roll_no",
        ]

    def validate_name(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Student name is required."
            )

        return value

    def validate_school_name(self, value):

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "School name is required."
            )

        return value

    def create(self, validated_data):

        student_class = validated_data[
            "student_class"
        ]

        roll_no = generate_student_roll_no(
            student_class
        )

        validated_data["roll_no"] = roll_no

        return Student.objects.create(
            **validated_data
        )