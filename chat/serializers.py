from rest_framework import serializers
from django.db.models import Count

from match.serializers import ProfileMinimalSerializer
from .models import *

class ChatSerializer(serializers.ModelSerializer):
    participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'participant', 'last_activity', 'last_message',  'is_active']

    def get_participant(self, obj):
        user = None
        request = self.context.get('request')
        if request:
            user = request.user
        else:
            user = self.context.get('user')

        if not user:
           user = obj.user2
        other_user = obj.user2 if user == obj.user1 else obj.user1
        return  ProfileMinimalSerializer(other_user.profile).data
    

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MiniMessageSerializer(last_message).data
        # {
        #         'content': last_message.content,
        #         'timestamp': last_message.created_at,
        #         'sender_id': str(last_message.sender.id)
        #     }
        return None

    # def get_unread_count(self, obj):
    #     user = self.context['request'].user
    #     return obj.messages.filter(read_at__isnull=True).exclude(sender=user).count()



class MiniMessageSerializer(serializers.ModelSerializer):
    is_pinned = serializers.SerializerMethodField()
    pin_count = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['chat', 'id', 'sender', 'content', 'content_type', 'created_at', 'read_at', 
                  'reactions','is_pinned', 'pin_count']
   
    def get_reactions(self, obj):
        """Aggregate reactions with emoji counts from MessageReaction model"""
        # reactions = obj.reactions.values('emoji').annotate(
        #     total=Count('emoji')
        # ).order_by('-total')
        
        return obj.reactions if obj.reactions else {}
    # {item['emoji']: item['total'] for item in reactions}

    # def get_reactions(self, obj):
    #     """Aggregate reactions with emoji counts from MessageReaction model"""
    #     reactions = obj.message_reactions.values('emoji').annotate(
    #         total=Count('emoji')
    #     ).order_by('-total')
        
    #     return {item['emoji']: item['total'] for item in reactions}

    def get_is_pinned(self, obj):
        """Check if current user has pinned this message"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.pinned_messages.filter(user=request.user).exists()
        return False

    def get_pin_count(self, obj):
        """Get total number of users who pinned this message"""
        return obj.pinned_messages.count()

class MessageRequestSerializer(serializers.ModelSerializer):
    participant = serializers.SerializerMethodField()
    class Meta:
        model = MessageRequest
        fields = ['id', 'participant', 'receiver', 'status', 'message', 'created_at']

    
    # def get_participant(self, obj):
    #     # Get user from context, either from request or direct context
    #     user = None
    #     request = self.context.get('request')
    #     if request:
    #         user = request.user
    #     else:
    #         user = self.context.get('user')
        
    #     if not user:
    #         return None
            
    #     # Get the other user (receiver or sender)
    #     other_user = obj.receiver if user == obj.sender else obj.sender
    #     if not other_user:
    #         return None
            
    #     return ProfileMinimalSerializer(other_user.profile).data
    def get_participant(self, obj):
        user = self.context.get('request').user if 'request' in self.context else self.context.get('user')
        
        if not user:
            return None

        # Determine the other user (receiver or sender)
        other_user = obj.receiver if user == obj.sender else obj.sender
        if not other_user:
            return None

        # Check if the other user has a profile
        if hasattr(other_user, 'profile'):
            return ProfileMinimalSerializer(other_user.profile).data
        else:
            return None
        

    