from rest_framework import serializers
from .models import AppConfiguration

class AppConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfiguration
        fields = ['key', 'value', 'version', 'last_updated']