# serializers.py (gift app)
from rest_framework import serializers
from .models import GiftType, VirtualGift
from django.conf import settings

class GiftTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    animation_url = serializers.SerializerMethodField()

    class Meta:
        model = GiftType
        fields = ['id', 'key', 'name', 'coin_price', 'image_url', 'animation_url']
        read_only_fields = fields

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_animation_url(self, obj):
        return obj.animation.url if obj.animation else None

class VirtualGiftSerializer(serializers.ModelSerializer):
    gift_type = GiftTypeSerializer(read_only=True)
    sender = serializers.StringRelatedField()
    receiver = serializers.StringRelatedField()

    class Meta:
        model = VirtualGift
        fields = ['id', 'gift_type', 'message', 'coins_value', 
                'timestamp', 'sender', 'receiver']
        read_only_fields = fields

class SendGiftSerializer(serializers.Serializer):
    gift_type_id = serializers.IntegerField()
    receiver_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        try:
            data['gift_type'] = GiftType.objects.get(pk=data['gift_type_id'], is_active=True)
        except GiftType.DoesNotExist:
            raise serializers.ValidationError("Invalid gift type")
        
        try:
            data['receiver'] = settings.AUTH_USER_MODEL.objects.get(pk=data['receiver_id'])
        except settings.AUTH_USER_MODEL.DoesNotExist:
            raise serializers.ValidationError("Receiver not found")
        
        if data['receiver'] == self.context['request'].user:
            raise serializers.ValidationError("Cannot send gift to yourself")
        
        return data