# admin.py
from django.contrib import admin
from .models import (
    User, Profile, UserPhoto, UserVideo, UserBlock,
    Interest, UserRating, UserAudioRecording, VideoPreference
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'email_verified', 'phone_verified','created_at')
    readonly_fields = ('id','old_id',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'gender', 'date_of_birth', 'user_status')
    search_fields = ('user__username', 'display_name')
    list_filter = ('gender', 'user_status', 'is_verified', 'user_type')
    filter_horizontal = ('interests',)

@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('user__username', 'caption')

@admin.register(UserVideo)
class UserVideoAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'video_type', 'duration', 'view_count')
    list_filter = ('video_type', 'is_public', 'created_at')
    search_fields = ('user__username', 'title', 'description')

@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')
    search_fields = ('user__username', 'blocked_user__username')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('rating_user', 'rated_user', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('rating_user__user__username', 'rated_user__user__username')

@admin.register(UserAudioRecording)
class UserAudioRecordingAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'duration', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('user__username', 'title', 'description')

@admin.register(VideoPreference)
class VideoPreferenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'video_quality', 'autoplay_videos', 'save_to_device')
    list_filter = ('video_quality', 'autoplay_videos', 'save_to_device')
    search_fields = ('profile__user__username',)