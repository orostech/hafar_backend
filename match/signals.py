# In match/models.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import MessageRequest
from django.db.models import Q

from .models import Match

@receiver(post_save, sender=Match)
def accept_message_requests_on_match(sender, instance, created, **kwargs):
    if created:
        # Check for pending message requests between these users
        MessageRequest.objects.filter(
            (Q(sender=instance.user1, receiver=instance.user2) |
            Q(sender=instance.user2, receiver=instance.user1)),
            status='PENDING'
        ).update(status='ACCEPTED')  # This will trigger the accept() method