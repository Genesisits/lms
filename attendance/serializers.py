from django.conf import settings
from rest_framework import serializers

from attendance.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    schedule = serializers.DateField(format=settings.DATE_FORMAT)

    class Meta:
        model = Attendance
        fields = '__all__'
