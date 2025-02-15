from django.contrib import admin
from .models import GiftType, VirtualGift

class GiftTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'coin_price', 'key', 'created_at']
    search_fields = ['name', 'key']
    list_filter = ['is_active']

class VirtualGiftAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'gift_type', 'timestamp']
    search_fields = ['sender__username', 'receiver__username', 'gift_type__name']
    list_filter = ['timestamp']

admin.site.register(GiftType, GiftTypeAdmin)
admin.site.register(VirtualGift, VirtualGiftAdmin)