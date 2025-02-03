from django.contrib import admin
from .models import Chat, Message, MessageReaction, PinnedMessage, ChatSettings, MessageRequest


class MessageInline(admin.StackedInline):
    model = Message
    extra = 0

class ChatSettingsInline(admin.StackedInline):
    model = ChatSettings
    extra = 0

class PinnedMessageInline(admin.StackedInline):
    model = PinnedMessage
    extra = 0

class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'match', 'created_at', 'last_activity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user1__name', 'user2__name', 'match__id')
    ordering = ['last_activity']
    inlines = [MessageInline, ChatSettingsInline]

class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'content_type', 'content', 'created_at', 'read_at')
    list_filter = ('content_type',)
    search_fields = ('content',)
    ordering = ['created_at']

class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'emoji', 'created_at')
    ordering = ['created_at']

class PinnedMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'user', 'pinned_at')
    ordering = ['pinned_at']

class ChatSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'chat', 'theme', 'custom_theme', 'notification_enabled')
    # ordering = ['created_at']

class MessageRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    ordering = ['created_at']

admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(MessageReaction, MessageReactionAdmin)
admin.site.register(PinnedMessage, PinnedMessageAdmin)
admin.site.register(ChatSettings, ChatSettingsAdmin)
admin.site.register(MessageRequest, MessageRequestAdmin)