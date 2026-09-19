from rest_framework import serializers


class Student14DayRecordSerializer(serializers.Serializer):
    date = serializers.DateField()
    day = serializers.CharField()
    attendance_status = serializers.CharField()
    session_id = serializers.IntegerField(allow_null=True)
    holiday_name = serializers.CharField(allow_null=True, allow_blank=True)
    homework_total = serializers.IntegerField()
    homework_completed = serializers.IntegerField()
    homework_pending = serializers.IntegerField()
    homework_xp = serializers.IntegerField()
    total_xp_earned = serializers.IntegerField()
    is_today = serializers.BooleanField()


class Student14DayHistorySerializer(serializers.Serializer):
    student = serializers.DictField()
    period = serializers.DictField()
    records = Student14DayRecordSerializer(many=True)
