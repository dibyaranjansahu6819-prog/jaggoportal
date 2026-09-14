from rest_framework import serializers

from students.models import Student
from teachers.models import Teacher
from .models import AttendancePhoto

from .models import (
    StudentAttendance,
    TeacherAttendance,
    Volunteer,
    VolunteerAssignment,
    PresentVolunteerAssignment,
)


class StudentAttendanceSerializer(serializers.ModelSerializer):

    roll_no = serializers.CharField(
        source="student.roll_no",
        read_only=True
    )

    student_name = serializers.CharField(
        source="student.name",
        read_only=True
    )

    student_class = serializers.CharField(
        source="student.student_class",
        read_only=True
    )

    class Meta:
        model = StudentAttendance
        fields = [
            "id",
            "student",
            "roll_no",
            "student_name",
            "student_class",
            "date",
            "status",
            "marked_at",
        ]
        read_only_fields = [
            "id",
            "roll_no",
            "student_name",
            "student_class",
            "marked_at",
        ]


class TeacherAttendanceSerializer(serializers.ModelSerializer):

    user_id = serializers.CharField(
        source="teacher.user_id",
        read_only=True
    )

    teacher_name = serializers.CharField(
        source="teacher.name",
        read_only=True
    )

    subject = serializers.CharField(
        source="teacher.subject.name",
        read_only=True
    )

    class Meta:
        model = TeacherAttendance
        fields = [
            "id",
            "teacher",
            "user_id",
            "teacher_name",
            "subject",
            "date",
            "status",
            "marked_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "teacher_name",
            "subject",
            "marked_at",
        ]


class VolunteerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Volunteer
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


class VolunteerAssignmentSerializer(serializers.ModelSerializer):

    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True
    )

    group_name = serializers.CharField(
        source="get_group_display",
        read_only=True
    )

    class Meta:
        model = VolunteerAssignment
        fields = [
            "id",
            "volunteer",
            "volunteer_name",
            "group",
            "group_name",
            "assigned_at",
        ]
        read_only_fields = [
            "id",
            "volunteer_name",
            "group_name",
            "assigned_at",
        ]


class PresentVolunteerAssignmentSerializer(
    serializers.ModelSerializer
):

    volunteer_name = serializers.CharField(
        source="volunteer.name",
        read_only=True
    )

    class Meta:
        model = PresentVolunteerAssignment
        fields = [
            "id",
            "student",
            "volunteer",
            "volunteer_name",
            "date",
            "assigned_at",
        ]
        read_only_fields = [
            "id",
            "volunteer_name",
            "assigned_at",
        ]
        

class AttendancePhotoSerializer(
    serializers.ModelSerializer
):

    url = serializers.SerializerMethodField()


    class Meta:

        model = AttendancePhoto

        fields = [
            "id",
            "photo",
            "url",
            "photo_type",
            "date",
            "uploaded_at",
        ]

        read_only_fields = [
            "id",
            "url",
            "uploaded_at",
        ]


    def get_url(
        self,
        obj
    ):

        request = self.context.get(
            "request"
        )

        if request:

            return request.build_absolute_uri(
                obj.photo.url
            )

        return obj.photo.url