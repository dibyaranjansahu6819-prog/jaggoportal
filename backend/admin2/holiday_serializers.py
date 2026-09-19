from rest_framework import serializers

from attendance.models import Holiday


class HolidaySerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Holiday
        fields = [
            "id",
            "date",
            "name",
            "is_active",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError(
                "Holiday name is required."
            )

        return value

    def validate_date(self, value):
        """
        Prevent duplicate holiday dates.

        The Holiday model already has a unique constraint on date,
        but this gives the API a clean validation message.
        """

        queryset = Holiday.objects.filter(
            date=value,
        )

        instance = self.instance

        if instance:
            queryset = queryset.exclude(
                pk=instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A holiday already exists for this date."
            )

        return value