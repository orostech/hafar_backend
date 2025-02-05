# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from users.const import RELATIONSHIP_CHOICES
from .models import (
    Profile, UserPhoto, UserVideo, UserBlock, Interest,
    UserRating, UserAudioRecording, VideoPreference
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'phone', 'email_verified', 'phone_verified')
        read_only_fields = ('email_verified', 'phone_verified','created_at')
        


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password',
                  #   'confirm_password',
                  #   'first_name',
                  #  'last_name', 'phone'
                  )

    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         raise serializers.ValidationError("Passwords don't match")
    #     return data

    def create(self, validated_data):
        # validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ('id', 'name')


class UserPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ('id', 'image', 'is_primary', 'order', 'caption',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


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


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    old_id = serializers.ReadOnlyField(source='user.old_id')
    # id = serializers.ReadOnlyField(source='user.id')
    # username = serializers.CharField(source='user.username', read_only=True)
    # of_interest = serializers.SerializerMethodField()
    # interests = InterestSerializer(many=True)
    # photos = UserPhotoSerializer(many=True, read_only=True)
    # videos = UserVideoSerializer(many=True, read_only=True)
    # video_preferences = VideoPreferenceSerializer(read_only=True)
    # average_rating = serializers.FloatField(read_only=True)
    # relationship_goal = serializers.ChoiceField(
    #     choice_classes=RELATIONSHIP_CHOICES,
    #     # source='relationship_goal',
    #     read_only=True
    # )

    class Meta:
        model = Profile
        fields = (
             # Information Level 1
            'id', 'old_id', 'username', 'display_name', 'bio', 'date_of_birth', 'gender', 'last_seen',
             # Information Level 2
            'interests', 'relationship_goal', 'interested_in',   'body_type',   'complexion', 'do_you_have_kids', 'do_you_have_pets', 'weight', 'height', 'dietary_preferences', 'smoking',
            'drinking', 'relationship_status', 'instagram_handle', 'facebook_link',
            # Information Level 3
            'latitude', 'longitude', 'address', 'state', 'country', 'profile_visibility', 'show_online_status', 'show_distance',
            'user_type', 'is_verified',  'user_status','show_last_seen'
              )
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_seen')

    def update(self, instance, validated_data):
        interests_data = validated_data.pop('interests', [])
        instance = super().update(instance, validated_data)

        if interests_data:
            instance.interests.clear()
            for interest_data in interests_data:
                interest, _ = Interest.objects.get_or_create(**interest_data)
                instance.interests.add(interest)

        return instance


class ProfileDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    of_interest = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('id', 'username', 'display_name', 'bio', 'date_of_birth', 'gender', 'body_type',
                  'user_type', 'is_verified', 'user_status', 'relationship_goal', 'interested_in',
                  'complexion', 'do_you_have_kids', 'do_you_have_pets', 'weight', 'height',
                  'dietary_preferences', 'smoking', 'drinking', 'relationship_status',
                  'instagram_handle', 'facebook_link', 'created_at', 'updated_at', 'last_seen')
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_seen')

    def get_of_interest(self, obj):
        # Add any custom logic here if needed
        return obj.interests.count()  # For example, you can show the count of interests


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


class CurrentUserProfileSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='user.id')
    username = serializers.CharField(source='user.username', read_only=True)
    old_id = serializers.ReadOnlyField(source='user.old_id')
    phone = serializers.ReadOnlyField(source='user.phone')
    email_verified = serializers.ReadOnlyField(source='user.email_verified')
    phone_verified  = serializers.ReadOnlyField(source='user.phone_verified')
    device_token  = serializers.ReadOnlyField(source='user.device_token')

    class Meta:
        model = Profile
        fields = (
            # Information Level 1
            'id', 'old_id', 'username', 'display_name', 'bio', 'date_of_birth', 'gender', 'phone', 'email_verified', 'phone_verified', 'device_token', 'created_at', 'updated_at', 'last_seen',
            # Information Level 2
            'interests','profession', 'relationship_goal', 'interested_in',   'body_type',   'complexion', 'do_you_have_kids', 'do_you_have_pets', 'weight', 'height', 'dietary_preferences', 'smoking',
            'drinking', 'relationship_status', 'instagram_handle',   'facebook_link',
            # Information Level 3
            'latitude', 'longitude', 'address', 'state', 'country', 'selected_address', 'selected_state', 'selected_country', 'selected_lga', 'profile_visibility', 'show_online_status', 'show_distance',
            'user_type', 'is_verified',  'user_status', 'minimum_age_preference', 'maximum_age_preference', 'maximum_distance_preference', 'show_last_seen',
            # Information Level 4
            'email_notifications', 'push_notifications', 'in_app_notifications' , 'new_matches_notitication','new_messages_notitication', 'app_updates', 'profile_view_notitication',
            'likes_received_notitication'

        )
        read_only_fields = (
            'user', 'created_at', 'updated_at', 'last_seen',
        )
