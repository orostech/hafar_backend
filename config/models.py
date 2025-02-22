from django.db import models
# from django_cryptography.fields import encrypt

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
    
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='other')
    platform = models.CharField(max_length=10, choices=[('all', 'All'), ('android', 'Android'), ('ios', 'iOS')], default='all')
    data = models.JSONField()
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
    message = models.TextField()
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

