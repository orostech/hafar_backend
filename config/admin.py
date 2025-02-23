# admin.py
from django.contrib import admin
from django_jsonform.widgets import JSONFormWidget
from .models import AppConfiguration, AppMaintenance
from django.db import models


@admin.register(AppConfiguration)
class AppConfigurationAdmin(admin.ModelAdmin):
    list_display = ('config_type', 'platform', 'version', 'is_active')
    list_filter = ('config_type', 'platform', 'is_active')
    formfield_overrides = {
        models.JSONField: {'widget': JSONFormWidget(schema={
            'type': 'object', 
        'properties': {},
            'additionalProperties': True
        })},
    }


@admin.register(AppMaintenance)
class AppMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('platform', 'is_active', 'start_time', 'end_time')
    list_filter = ('platform', 'is_active')
