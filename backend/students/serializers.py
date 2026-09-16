from rest_framework import serializers

from .models import Student
from .utils import generate_student_roll_no


class StudentRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = [
            "roll_no",
            "name",
            "student_class",
            "school_name",
            "created_at",
        ]
        read_only_fields = [
            "roll_no",
            "created_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Student name cannot be empty."
            )

        return value

    def validate_school_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "School name cannot be empty."
            )

        return value

    def create(self, validated_data):
        student_class = validated_data["student_class"]

        roll_no = generate_student_roll_no(student_class)

        return Student.objects.create(
            roll_no=roll_no,
            **validated_data,
        )