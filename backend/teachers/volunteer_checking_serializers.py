from rest_framework import serializers

from .models import StudentChecking


class StudentCheckingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.name",
        read_only=True,
    )

    student_roll_no = serializers.CharField(
        source="student.roll_no",
        read_only=True,
    )

    student_class = serializers.CharField(
        source="student.student_class",
        read_only=True,
    )

    class Meta:
        model = StudentChecking

        fields = [
            "id",
            "assignment",
            "work_session",
            "volunteer",
            "student",
            "student_name",
            "student_roll_no",
            "student_class",
            "homework_status",
            "feedback",
            "checked_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "assignment",
            "work_session",
            "volunteer",
            "student_name",
            "student_roll_no",
            "student_class",
            "checked_at",
            "created_at",
        ]

    def validate_homework_status(self, value):
        allowed = {
            "DONE",
            "NOT_DONE",
        }

        if value not in allowed:
            raise serializers.ValidationError(
                "Homework status must be DONE or NOT_DONE."
            )

        return value

    def validate_feedback(self, value):
        return value.strip()