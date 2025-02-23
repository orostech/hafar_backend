# match/admin.py
from django.contrib import admin
from .models import Like, Dislike, Match, SwipeLimit, UserPreferenceWeight, UserSwipeAction, Visit

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('liker', 'liked', 'like_type', 'created_at', 'is_active')
    search_fields = ('liker__username', 'liked__username')
    autocomplete_fields = ['liker', 'liked']
    list_filter = ('like_type', 'is_active')
    readonly_fields = ('created_at',)

@admin.register(Dislike)
class DislikeAdmin(admin.ModelAdmin):
    list_display = ('disliker', 'disliked', 'created_at')
    search_fields = ('disliker__username', 'disliked__username')
    autocomplete_fields = ['disliker', 'disliked']
    readonly_fields = ('created_at',)

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('visitor', 'visited', 'created_at')
    search_fields = ('visitor__username', 'visited__username')
    autocomplete_fields = ['visitor', 'visited']
    readonly_fields = ('created_at',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at', 'is_active', 'last_interaction')
    search_fields = ('user1__username', 'user2__username')
    autocomplete_fields = ['user1', 'user2']
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'last_interaction')

@admin.register(SwipeLimit)
class SwipeLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_likes_count', 'daily_super_likes_count', 'last_reset')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    readonly_fields = ('last_reset',)

@admin.register(UserPreferenceWeight)
class UserPreferenceWeightAdmin(admin.ModelAdmin):
    list_display = ('user', 'distance_weight', 'age_weight', 'interests_weight', 'lifestyle_weight')
    search_fields = ('user__username',)
    list_filter = ('distance_weight', 'age_weight', 'interests_weight', 'lifestyle_weight')

@admin.register(UserSwipeAction)
class UserSwipeActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_user', 'action', 'created_at', 'target_age', 'target_distance')
    search_fields = ('user__username', 'target_user__username', 'action')
    list_filter = ('action',)
    readonly_fields = ('created_at',)