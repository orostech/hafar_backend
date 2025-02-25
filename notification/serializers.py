# serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'verb', 'target_id', 'read', 'created_at']
        read_only_fields = ['id', 'recipient', 'actor', 'verb', 'target_id', 'created_at']