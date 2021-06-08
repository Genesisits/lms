from rest_framework import serializers

from .models import *


class EmailTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailTemplates
        fields = "__all__"


class EmailNotificationsSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailNotifications
        fields = "__all__"
