from rest_framework import serializers

from .models import (
    AttendanceSession,
    StudentAttendance,
    VolunteerAttendance,
)


class AttendanceSessionSerializer(
    serializers.ModelSerializer
):

    has_expired = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession

        fields = [
            "id",
            "session_date",
            "started_at",
            "ended_at",
            "expires_at",
            "is_active",
            "has_expired",
        ]

        read_only_fields = [
            "id",
            "session_date",
            "started_at",
            "ended_at",
            "expires_at",
            "is_active",
            "has_expired",
        ]

    def get_has_expired(self, obj):
        return obj.has_expired


class StudentAttendanceSerializer(
    serializers.ModelSerializer
):

    roll_no = serializers.CharField(
        source="student.roll_no",
        read_only=True,
    )

    student_name = serializers.CharField(
        source="student.name",
        read_only=True,
    )

    student_class = serializers.CharField(
        source="student.student_class",
        read_only=True,
    )

    class Meta:
        model = StudentAttendance

        fields = [
            "id",
            "session",
            "student",
            "roll_no",
            "student_name",
            "student_class",
            "status",
            "marked_at",
        ]

        read_only_fields = [
            "id",
            "session",
            "roll_no",
            "student_name",
            "student_class",
            "marked_at",
        ]


class VolunteerAttendanceSerializer(
    serializers.ModelSerializer
):

    user_id = serializers.CharField(
        source="volunteer.user_id",
        read_only=True,
    )

    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True,
    )

    subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    email = serializers.EmailField(
        source="volunteer.email",
        read_only=True,
    )

    subject = serializers.CharField(
        source="volunteer.subject.name",
        read_only=True,
    )

    class Meta:
        model = VolunteerAttendance

        fields = [
            "id",
            "session",
            "volunteer",
            "user_id",
            "volunteer_name",
            "email",
            "subject",
            "task",
            "attendance_source",
            "status",
            "marked_at",
        ]

        read_only_fields = [
            "id",
            "session",
            "user_id",
            "volunteer_name",
            "email",
            "subject",
            "attendance_source",
            "marked_at",
        ]