from rest_framework import serializers

from .models import StudentProgress


class StudentProgressSerializer(serializers.ModelSerializer):
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
        model = StudentProgress

        fields = [
            "id",
            "assignment",
            "work_session",
            "volunteer",
            "student",
            "student_name",
            "student_roll_no",
            "student_class",
            "performance",
            "feedback",
            "homework_given",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "assignment",
            "work_session",
            "volunteer",
            "student_name",
            "student_roll_no",
            "student_class",
            "created_at",
            "updated_at",
        ]

    def validate_performance(self, value):
        allowed = {
            "POOR",
            "AVERAGE",
            "GOOD",
        }

        if value not in allowed:
            raise serializers.ValidationError(
                "Performance must be POOR, AVERAGE, or GOOD."
            )

        return value

    def validate_feedback(self, value):
        return value.strip()