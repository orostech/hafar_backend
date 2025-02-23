from django.db import models
from django_jsonform.models.fields import JSONField
# from django_cryptography.fields import encrypt
# def get_schema(config_type):
    # Define different schemas based on config_type
    # schemas = {
    #     'ad_config': {
    #         'type': 'dict',
    #         'keys': {
    #             'ad_provider': {'type': 'string', 'title': 'Ad Provider'},
    #             'ad_unit_id': {'type': 'string', 'title': 'Ad Unit ID'},
    #         }
    #     },
    #     'app_versions': {
    #         'type': 'dict',
    #         'keys': {
    #             'android_version': {'type': 'string', 'title': 'Android Version'},
    #             'ios_version': {'type': 'string', 'title': 'iOS Version'},
    #         }
    #     },
    #     # Add more schemas as needed
    # }
    # return schemas.get(config_type, {'type': 'dict'})  # Default to an empty dict if config_type is not found
class AppConfiguration(models.Model):
    CONFIG_TYPES = [
        ('ad_config', 'Ad Configuration'),
        ('app_versions', 'App Versions'),
        ('feature_flags', 'Feature Flags'),
        ('security', 'Security Keys'),
        ('app_settings', 'App Settings'),
        ('third_party', 'Third Party Services'),
        ('other', 'Not Assign Yet'),
    ]
    ITEMS_SCHEMA = {
        'type': 'dict', # a list which will contain the items
        'keys': {
            'key': {'type': 'string', 'title': 'key'},
            'value': {'type': 'string', 'title': 'value'},
            'hint': {'type': 'string', 'title': 'hint'},
            }
      
    }

    
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='other')
    platform = models.CharField(max_length=10, choices=[('all', 'All'), ('android', 'Android'), ('ios', 'iOS')], default='all')
    data = JSONField(schema=ITEMS_SCHEMA, blank=True)
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_secret = models.BooleanField(default=False)
    # encrypted_data = encrypt(models.JSONField(blank=True, null=True))
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version']
        unique_together = ['config_type', 'platform']

class AppMaintenance(models.Model):
    platform = models.CharField(max_length=10, choices=[('all', 'All'), ('android', 'Android'), ('ios', 'iOS')])
    message = models.TextField( default="Our app is currently undergoing maintenance to bring you an even better experience. We apologize for any inconvenience this may cause. Please check back later, and thank you for your patience!",)
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
# class AppConfiguration(models.Model):
#     key = models.CharField(max_length=100, unique=True)
#     value = models.JSONField()
#     version = models.IntegerField(default=1)
#     is_active = models.BooleanField(default=True)
#     last_updated = models.DateTimeField(auto_now=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-version']

