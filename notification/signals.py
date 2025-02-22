from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from .services import FirebaseNotificationService
from .email_service import EmailService
from match.models import Like, Visit, Match
from chat.models import Message  # Assuming you have a chat app
from .models import Notification
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()


def create_notification_and_send_push(recipient, actor, verb, target_id, 
                                     title_template, body_template,
                                     push_enabled_field, email_enabled=True):
    # Create in-app notification always
    if verb not in ['MESSAGE']:
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            target_id=target_id
        )

    # Check push notification preferences
    profile = recipient.profile
    if getattr(profile, push_enabled_field, False) and profile.push_notifications:
        try:
            FirebaseNotificationService.send_push_notification(
                recipient=recipient,
                title=title_template % actor.profile.display_name,
                body=body_template % actor.profile.display_name,
                data={
                    'type': verb,
                    'id': str(target_id),
                    'actor_id': str(actor.id)
                }
            )
        except Exception as e:
            logger.error(f"Firebase notification failed: {str(e)}")

@receiver(post_save, sender=Like)
def handle_like_notification(sender, instance, created, **kwargs):
    if created:
        try:
            verb = 'SUPER_LIKE' if instance.like_type == 'SUPER' else 'LIKE'
            title = "Super Like from %s!" if verb == 'SUPER_LIKE' else "New Like from %s!"
            body = "You've been super liked!" if verb == 'SUPER_LIKE' else "Someone likes you!"
            print('qwe 11')
            transaction.on_commit(lambda: create_notification_and_send_push(
                recipient=instance.liked,
                actor=instance.liker,
                verb=verb,
                target_id=instance.id,
                title_template=title,
                body_template=body,
                push_enabled_field='likes_received_notitication'
            ))
            print('qwe 1qw1')
        except Exception as e:
            logger.error(f"Like notification failed: {str(e)}")
        
        try:
            email_service.send_like_notification(instance)
        except Exception as e:
            logger.error(f"Like email notification failed: {str(e)}")

@receiver(post_save, sender=Visit)
def handle_visit_notification(sender, instance, created, **kwargs):
    if created:
        try:
            transaction.on_commit(lambda: create_notification_and_send_push(
                recipient=instance.visited,
                actor=instance.visitor,
                verb='VISIT',
                target_id=instance.id,
                title_template="%s viewed your profile",
                body_template="Someone checked out your profile",
                push_enabled_field='profile_view_notitication'
            ))
        except Exception as e:
            logger.error(f"Visit notification failed: {str(e)}")
        
        
        try:
            email_service.send_profile_view_notification(instance)
        except Exception as e:
            logger.error(f"Visit email notification failed: {str(e)}")

@receiver(post_save, sender=Match)
def handle_match_notification(sender, instance, created, **kwargs):
    if created:
        try:
            for user, other_user in [(instance.user1, instance.user2), 
                                   (instance.user2, instance.user1)]:
                transaction.on_commit(lambda: create_notification_and_send_push(
                    recipient=user,
                    actor=other_user,
                    verb='MATCH',
                    target_id=instance.id,
                    title_template="You matched with %s!",
                    body_template="It's a match! Start chatting with %s",
                    push_enabled_field='new_matches_notitication'
                ))
        except Exception as e:
            logger.error(f"Match notification failed: {str(e)}")

        try:
            email_service.send_match_notification(instance)
        except Exception as e:
            logger.error(f"Match email notification failed: {str(e)}")

@receiver(post_save, sender=Message)
def handle_message_notification(sender, instance, created, **kwargs):
    if created:
        try:
            chat = instance.chat
            recipient = chat.user2 if instance.sender == chat.user1 else chat.user1
            
            transaction.on_commit(lambda: create_notification_and_send_push(
                recipient=recipient,
                actor=instance.sender,
                verb='MESSAGE',
                target_id=instance.id,
                title_template="New message from %s",
                body_template=instance.content[:30] + "...",
                push_enabled_field='new_messages_notitication'
            ))
        except Exception as e:
            logger.error(f"Message notification failed: {str(e)}")




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