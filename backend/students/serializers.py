from rest_framework import serializers

from .models import StudentHomework,StudentXPTransaction


from .models import Student
from .utils import generate_student_roll_no


class StudentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student

        fields = [
            "roll_no",
            "name",
            "student_class",
            "group",
            "school_name",
            "created_at",
        ]

        read_only_fields = [
            "roll_no",
            "group",
            "created_at",
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
                "Student school name is required."
            )

        return value

    def create(self, validated_data):
        student_class = validated_data["student_class"]

        validated_data["roll_no"] = generate_student_roll_no(
            student_class
        )

        return Student.objects.create(
            **validated_data
        )
        
class StudentHomeworkCompletionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.name",
        read_only=True,
    )
    roll_no = serializers.CharField(
        source="student.roll_no",
        read_only=True,
    )
    student_class = serializers.CharField(
        source="student.student_class",
        read_only=True,
    )
    group = serializers.CharField(
        source="student.group",
        read_only=True,
    )

    class Meta:
        model = StudentHomework
        fields = [
            "id",
            "student",
            "student_name",
            "roll_no",
            "student_class",
            "group",
            "assignment",
            "work_session",
            "status",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "student",
            "student_name",
            "roll_no",
            "student_class",
            "group",
            "assignment",
            "work_session",
            "status",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        
class StudentXPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentXPTransaction
        fields = [
            "id",
            "points",
            "source",
            "reason",
            "homework",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "points",
            "source",
            "reason",
            "homework",
            "created_by",
            "created_at",
        ]


class StudentXPSerializer(serializers.Serializer):
    student = serializers.SerializerMethodField()
    total_xp = serializers.IntegerField()
    transaction_count = serializers.IntegerField()
    transactions = StudentXPTransactionSerializer(many=True)

    def get_student(self, obj):
        student = obj["student"]

        return {
            "id": student.id,
            "roll_no": student.roll_no,
            "name": student.name,
            "student_class": student.student_class,
            "group": student.group,
            "school_name": student.school_name,
        }
        
class StudentLeaderboardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student_id = serializers.IntegerField()
    roll_no = serializers.CharField()
    name = serializers.CharField()
    student_class = serializers.CharField()
    group = serializers.CharField()
    school_name = serializers.CharField()
    total_xp = serializers.IntegerField()