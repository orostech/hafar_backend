# serializer.py
from rest_framework import serializers
from .models import AppConfiguration, AppMaintenance

class AppConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppConfiguration
        fields = ['config_type', 'platform', 'data', 'version', 'last_updated']
        read_only_fields = ['version', 'last_updated']

class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppMaintenance
        fields = '__all__'