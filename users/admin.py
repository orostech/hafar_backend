# admin.py
from django.contrib import admin
from .models import (
    OTP, User, Profile, UserPhoto, UserVideo, UserBlock, Rating, UserAudioRecording, VideoPreference
)

from django.contrib import admin
from users.models import State, LGA

class LGAInline(admin.TabularInline):  # Allows editing LGAs within the State admin page
    model = LGA
    extra = 1  # Number of empty forms to display

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "alias")  # Display state name and alias in the admin list
    search_fields = ("name", "alias")  # Enable searching by name or alias
    inlines = [LGAInline]  # Show LGAs inside the State page

@admin.register(LGA)
class LGAAdmin(admin.ModelAdmin):
    list_display = ("name", "state")  # Show LGA name and its state in the list
    search_fields = ("name",)
    list_filter = ("state",)  # Add filtering by state in the admin panel
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('created_at','is_active', 'is_staff', 'email_verified', 'phone_verified')
    readonly_fields = ('id','old_id',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'gender', 'date_of_birth', 'user_status')
    search_fields = ('user__username', 'display_name')
    list_filter = ('gender', 'user_status', 'is_verified', 'user_type', 'created_at')
    readonly_fields = ('updated_at', 'created_at')
    autocomplete_fields = ('user',)

@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('user__username', 'caption')
    autocomplete_fields = ('user',)

@admin.register(UserVideo)
class UserVideoAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'video_type', 'duration', 'view_count')
    list_filter = ('video_type', 'is_public', 'created_at')
    search_fields = ('user__username', 'title', 'description')
    autocomplete_fields = ('user',)

@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('user', 'blocked_user', 'created_at')
    search_fields = ('user__username', 'blocked_user__username')
    autocomplete_fields = ('user', 'blocked_user')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rating_user', 'rated_user', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('rating_user__user__username', 'rated_user__user__username')
    autocomplete_fields = ('rating_user', 'rated_user')

@admin.register(UserAudioRecording)
class UserAudioRecordingAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'duration', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('user__username', 'title', 'description')
    autocomplete_fields = ('user',)

@admin.register(VideoPreference)
class VideoPreferenceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'video_quality', 'autoplay_videos', 'save_to_device')
    list_filter = ('video_quality', 'autoplay_videos', 'save_to_device')
    search_fields = ('profile__user__username',)
    autocomplete_fields = ('profile',)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
    autocomplete_fields = ('user',)
    