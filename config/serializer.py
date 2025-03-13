# serializer.py
from rest_framework import serializers

from match.serializers import ProfileMinimalSerializer
from users.models import Profile
from users.serializers import ProfileSerializer
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

class AdminProfileSerializer(ProfileSerializer):
    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + tuple(['user_status', 'is_verified'])
        read_only_fields = ProfileSerializer.Meta.read_only_fields

class AdminProfileListSerializer(ProfileMinimalSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    email = serializers.ReadOnlyField(source='user.email')
    profile_photo = serializers.ReadOnlyField(source='user.get_profile_photo')
    average_rating = serializers.ReadOnlyField(source='user.average_rating')
    created_at = serializers.ReadOnlyField(source='user.created_at')




    class Meta:
        model = Profile
        fields = ['id','email', 'display_name', 'profile_photo','created_at','average_rating','gender','state', 'country','user_status',
                'online_status','is_premium','latlng'
                  ]
    # def get_profile_photo(self, obj):
    #     photo = obj.user.photos.filter(is_primary=True).first()
    #     if photo:
    #         if not photo.image:
    #             return photo.image_url
    #         return photo.image.url
    #     return None 
