from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('LIKE', 'Like'),
        ('SUPER_LIKE', 'Super Like'),
        ('MATCH', 'Match'),
        ('MESSAGE', 'Message'),
        ('VISIT', 'Profile Visit'),
    ]


    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acted_notifications')
    verb = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_id = models.PositiveIntegerField(null=True, blank=True)  # ID of related object (e.g., Match, Like)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.verb}"

    class Meta:
        ordering = ['-created_at']