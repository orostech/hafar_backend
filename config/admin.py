from django.contrib import admin

from .models import AppConfiguration

# Register your models here.
@admin.register(AppConfiguration)
class AppConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'version', 'created_at', 'is_active')
    search_fields = ('key',)
    list_filter = ('is_active',)
    readonly_fields = ('created_at',)
