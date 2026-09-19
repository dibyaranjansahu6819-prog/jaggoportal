from rest_framework import serializers

from .models import VolunteerWorkSession


class VolunteerWorkSessionSerializer(serializers.ModelSerializer):
    elapsed_seconds = serializers.SerializerMethodField()

    class Meta:
        model = VolunteerWorkSession
        fields = [
            "id",
            "assignment",
            "volunteer",
            "started_at",
            "ended_at",
            "total_seconds",
            "elapsed_seconds",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_elapsed_seconds(self, obj):
        if obj.status == "COMPLETED":
            return obj.total_seconds or 0

        if obj.status == "IN_PROGRESS" and obj.started_at:
            from django.utils import timezone

            elapsed = timezone.now() - obj.started_at
            return max(0, int(elapsed.total_seconds()))

        return 0


class VolunteerAssignmentDashboardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    assignment_date = serializers.DateField()
    assigned_class = serializers.CharField()
    task = serializers.CharField()
    instruction = serializers.CharField()
    attachment = serializers.SerializerMethodField()
    homework_attachment = serializers.SerializerMethodField()
    email_status = serializers.CharField()
    work_session = VolunteerWorkSessionSerializer(allow_null=True)

    def get_attachment(self, obj):
        if not obj.attachment:
            return None

        request = self.context.get("request")

        try:
            url = obj.attachment.url
        except ValueError:
            return None

        if request:
            return request.build_absolute_uri(url)

        return url

    def get_homework_attachment(self, obj):
        if not obj.homework_attachment:
            return None

        request = self.context.get("request")

        try:
            url = obj.homework_attachment.url
        except ValueError:
            return None

        if request:
            return request.build_absolute_uri(url)

        return url