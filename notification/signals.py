# notifications/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .email_service import EmailService
from match.models import Like, Visit, Match
from chat.models import Message  # Assuming you have a chat app
from .models import Notification
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()

@receiver(post_save, sender=Visit)
def handle_visit_notification(sender, instance, created, **kwargs):
    """Handle visit notifications and emails"""
    if created:
        try:
            def _create_notification():
                # Create notification
                Notification.objects.create(
                    recipient=instance.visited,
                    actor=instance.visitor,
                    verb='VISIT',
                    target_id=instance.id
                )
                # Send email notification
                if instance.visited.profile.email_notifications:
                    email_service.send_profile_view_notification(instance)
                
            transaction.on_commit(_create_notification)
            
        except Exception as e:
            logger.error(f"Visit notification handling failed: {str(e)}", exc_info=True)

@receiver(post_save, sender=Like)
def handle_like_notification(sender, instance, created, **kwargs):
    """Handle like notifications and emails"""
    if created:
        try:
            def _create_notification():
                verb = 'SUPER_LIKE' if instance.like_type == 'SUPER' else 'LIKE'
                # Create notification
                Notification.objects.create(
                    recipient=instance.liked,
                    actor=instance.liker,
                    verb=verb,
                    target_id=instance.id
                )
                # Send email notification
                email_service.send_like_notification(instance)
                
            transaction.on_commit(_create_notification)
            
        except Exception as e:
            logger.error(f"Like notification handling failed: {str(e)}", exc_info=True)

@receiver(post_save, sender=Match)
def handle_match_notification(sender, instance, created, **kwargs):
    """Handle match notifications and emails"""
    if created:
        try:
            def _create_notifications():
                # Create notifications for both users
                for user in [instance.user1, instance.user2]:
                    other_user = instance.user2 if user == instance.user1 else instance.user1
                    Notification.objects.create(
                        recipient=user,
                        actor=other_user,
                        verb='MATCH',
                        target_id=instance.id
                    )
                # Send email notifications
                email_service.send_match_notification(instance)
                
            transaction.on_commit(_create_notifications)
            
        except Exception as e:
            logger.error(f"Match notification handling failed: {str(e)}", exc_info=True)

@receiver(post_save, sender=Message)
def handle_message_notification(sender, instance, created, **kwargs):
    """Handle message notifications and emails"""
    if created:
        try:
            def _create_notification():
                # Create notification
                Notification.objects.create(
                    recipient=instance.recipient,
                    actor=instance.sender,
                    verb='MESSAGE',
                    target_id=instance.id
                )
                # Send email notification
                email_service.send_message_notification(instance)
                
            transaction.on_commit(_create_notification)
            
        except Exception as e:
            logger.error(f"Message notification handling failed: {str(e)}", exc_info=True)