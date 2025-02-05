from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('LIKE', 'Like'),
        ('MATCH', 'Match'),
        ('VISIT', 'Profile Visit'),
        ('MESSAGE', 'New Message'),
        ('SUPER_LIKE', 'Super Like'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acted_notifications')
    verb = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_id = models.PositiveIntegerField(null=True, blank=True)  # ID of related object (e.g., Match, Like)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']