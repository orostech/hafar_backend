# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from subscription.serializers import UserSubscriptionSerializer
from users.const import RELATIONSHIP_CHOICES
from wallet.serializers import WalletSerializer
from .models import (
    LGA, Profile, State, UserPhoto, UserVideo, UserBlock,
    UserRating, UserAudioRecording, VideoPreference
)

User = get_user_model()

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name"]

class LGASerializer(serializers.ModelSerializer):
    class Meta:
        model = LGA
        fields = ["id", "name", "state"]

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('email', 'password', )


    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserPhotoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = UserPhoto
        fields = ('id', 'image', 'is_primary', 'order', 'caption',
                  'created_at', 'updated_at'           )
        read_only_fields = ('created_at', 'updated_at')

    def get_image(self, obj):
        request = self.context.get('request')
        if not obj.image:
            return obj.image_url
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url



class UserVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVideo
        fields = ('id', 'video_file', 'thumbnail', 'title', 'description',
                  'duration', 'video_type', 'is_public', 'view_count',
                  'created_at', 'updated_at')
        read_only_fields = ('view_count', 'created_at', 'updated_at')


class UserAudioRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAudioRecording
        fields = ('id', 'audio_file', 'title', 'description', 'duration',
                  'is_public', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class VideoPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPreference
        fields = ('id', 'autoplay_videos', 'video_quality', 'save_to_device')

class UserBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBlock
        fields = ('id', 'blocked_user', 'reason', 'created_at')
        read_only_fields = ('created_at',)


class UserRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = ('id', 'rated_user', 'value', 'created_at')
        read_only_fields = ('created_at',)

class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    old_id = serializers.ReadOnlyField(source='user.old_id')
    photos = UserPhotoSerializer(source='user.photos',many=True, read_only=True)
    age = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    is_new_user = serializers.SerializerMethodField()
    online_status= serializers.SerializerMethodField()
    latlng = serializers.SerializerMethodField()
    selected_state = StateSerializer(read_only=True)
    selected_lga = LGASerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            
                # Information Level 1
                'id', 'old_id', 'username', 'display_name', 'bio', 'date_of_birth','age', 'gender', 'photos','average_rating','body_type','last_seen', 'is_premium',
                # Information Level 2 
                #  'interests',
                 'profession', 'relationship_goal','relationship_status', 'interested_in',   'body_type',   'complexion', 'do_you_have_kids', 'do_you_have_pets', 'weight', 'height','drinking', 'dietary_preferences', 'smoking',   
                # Information Level 3
                'latlng', 'address', 'state', 'country', 'selected_address', 'selected_state','selected_lga', 'selected_country', 'selected_lga','show_online_status', 'show_distance',
                'user_type', 'is_verified',  'user_status', 'minimum_age_preference', 'maximum_age_preference', 'maximum_distance_preference', 'show_last_seen','is_new_user','online_status',)
        
        
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_seen',)

    def get_latlng(self, obj):
        return obj.latlng()
    
    def get_average_rating(self, obj):
        return obj.user.average_rating
    
    def get_is_premium(self, obj):
        return obj.user.active_subscription is not None
    
    def get_age(self, obj):
        return obj.get_age()
        
    def get_is_new_user(self, obj):
        return obj.is_new_user

    def get_online_status(self,obj):
        return obj.online_status

       
    # def get_distance(self, obj):
    # # user = None
    #     request = self.context.get('request')
    #     print(request)
    #     print('m e 1mo')
    #     if request:
    #         user = request.user
    #     else:
    #         user = self.context.get('user')
    #     if hasattr(user.profile, 'location') and hasattr(obj, 'location') :
    #         print('m edkc 1')
    #         if obj.location and user.profile.location:
    #             print('m kx sde 1')
    #             m = obj.location.distance(request.user.profile.location) * 100  # km
    #             print(m)
    #             return m
    #     return None
class CurrentUserProfileSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    old_id = serializers.ReadOnlyField(source='user.old_id')
    phone = serializers.ReadOnlyField(source='user.phone')
    email_verified = serializers.ReadOnlyField(source='user.email_verified')
    phone_verified  = serializers.ReadOnlyField(source='user.phone_verified')
    device_token  = serializers.ReadOnlyField(source='user.device_token')
    photos = UserPhotoSerializer(source='user.photos',many=True, read_only=True)
    wallet = WalletSerializer(source='user.wallet', read_only=True)
    age = serializers.SerializerMethodField()
    subscription = UserSubscriptionSerializer(source='user.active_subscription', read_only=True)
    is_premium = serializers.SerializerMethodField()
    latlng = serializers.SerializerMethodField()
    selected_state = StateSerializer(read_only=True)
    selected_lga = LGASerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = (
            # Information Level 1
          
            'id', 'old_id', 'username', 'display_name', 'bio', 'date_of_birth','age', 'gender','photos','wallet', 'phone', 'email_verified', 'phone_verified', 'device_token', 'created_at', 'updated_at', 'last_seen',
            # Information Level 2
            # 'interests',
            'profession', 'relationship_goal', 'interested_in',   'body_type',   'complexion', 'do_you_have_kids', 'do_you_have_pets', 'weight', 'height', 'dietary_preferences', 'smoking',
            'drinking', 'relationship_status', 'instagram_handle',   'facebook_link',
            # Information Level 3
            'latitude', 'longitude','latlng', 'address', 'state', 'country', 'selected_address', 'selected_state', 'selected_country', 'selected_lga', 'profile_visibility', 'show_online_status', 'show_distance',
            'user_type', 'is_verified',  'user_status', 'minimum_age_preference', 'maximum_age_preference', 'maximum_distance_preference', 'show_last_seen',
            # Information Level 4
            'email_notifications', 'push_notifications', 'in_app_notifications' , 'new_matches_notitication','new_messages_notitication', 'app_updates', 'profile_view_notitication',
            'likes_received_notitication','average_rating',

            # Infomation Level 7
            'subscription', 'is_premium'

        )
        read_only_fields = (
            'user', 'created_at', 'updated_at', 'last_seen',
        )

    def get_age(self, obj):
        return obj.get_age()
    
    def get_is_premium(self, obj):
        return obj.user.active_subscription is not None
    
    def get_latlng(self, obj):
        return obj.latlng()

    def get_average_rating(self, obj):
        return obj.average_rating

       



 