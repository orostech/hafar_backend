from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'target_id', 'read', 'created_at')
    list_filter = ('verb', 'read', 'created_at')
    search_fields = ('recipient__username', 'actor__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
