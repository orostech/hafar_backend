# serializers.py
from rest_framework import serializers
from match.serializers import ProfileMinimalSerializer
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    profile = ProfileMinimalSerializer(source='actor.profile', read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor','profile', 'verb', 'target_id', 'read', 'created_at']
        read_only_fields = ['id', 'recipient', 'actor',
         'verb', 'target_id', 'created_at']