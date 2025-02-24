from datetime import timezone
from functools import partial
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from chat.serializers import ChatSerializer, MessageRequestSerializer, MiniMessageSerializer
from match.serializers import ProfileMinimalSerializer

from .services import FirebaseNotificationService
from .email_service import EmailService
from match.models import Like, Visit, Match
from chat.models import Chat, Message, MessageRequest  # Assuming you have a chat app
from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()

def send_ws_notification(user_id, action_type, data):
    # print(data)
    if 'profile' in data and 'id' in data['profile']:
        data['profile']['id'] = str(data['profile']['id'])
    print(data)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'send_activity',
            'action_type': action_type,
            'data': json.loads(json.dumps(data, default=str)),
            # data,
        }
    )


def create_notification_and_send_push(recipient, actor, verb, target_id, 
                                     title_template, body_template,
                                     push_enabled_field, email_enabled=True,data=None):
    # Create in-app notification always
    if verb not in ['MESSAGE','CHAT','REQUEST_ACCEPTED','NEW_REQUEST']:
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            target_id=target_id
        )

    # Check push notification preferences
    profile = recipient.profile
    profileData = ProfileMinimalSerializer(profile).data
    title = title_template % actor.profile.display_name if "%s" in title_template else title_template
    body = body_template % actor.profile.display_name if "%s" in body_template else body_template
           
    if getattr(profile, push_enabled_field, False) and profile.push_notifications:
        try:
            # title = title_template % actor.profile.display_name if "%s" in title_template else title_template
            # body = body_template % actor.profile.display_name if "%s" in body_template else body_template
            FirebaseNotificationService.send_push_notification(
                recipient=recipient,
                title=title,
                body=body,
                data={
                    'type': verb,
                    'id': str(target_id),
                    'actor_id': str(actor.id),
                    'profile':profileData
                }
            )
        except Exception as e:
            logger.error(f"Firebase notification failed: {str(e)}")

     # Prepare WebSocket data
    ws_data = {
        'type': verb,
        'message': body,
        'title':title,
        # 'display_name': actor.profile.display_name,
        # 'profile_photo':
        'target_id':target_id
    }

    if data is not None:
        ws_data.update(data)
    else:
        ws_data['profile'] = profileData

    send_ws_notification(
        recipient.id, 
        'notification',
        ws_data
    )
    # send_ws_notification(
    #     recipient.id, 
    #     'notification',
    #     {'type': verb, 'message': body_template, 'profile':profileData}
    # )


@receiver(post_save, sender=Like)
def handle_like_notification(sender, instance, created, **kwargs):
   
    if created:
        try:
            verb = 'SUPER_LIKE' if instance.like_type == 'SUPER' else 'LIKE'
            title = "Super Like from %s!" if verb == 'SUPER_LIKE' else "New Like from %s!"
            body = "You've been super liked!" if verb == 'SUPER_LIKE' else "Someone likes you!"
            transaction.on_commit(lambda: create_notification_and_send_push(
                recipient=instance.liked,
                actor=instance.liker,
                verb=verb,
                target_id=instance.id,
                title_template=title,
                body_template=body,
                push_enabled_field='likes_received_notitication'
            ))
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
                notification_task = partial(
                    create_notification_and_send_push,
                    recipient=user,
                    actor=other_user,
                    verb='MATCH',
                    target_id=instance.id,
                    title_template="You matched with %s!",
                    body_template="It's a match! Start chatting with %s",
                    push_enabled_field='new_matches_notitication'
                )
                transaction.on_commit(notification_task)
        except Exception as e:
            logger.error(f"Match notification failed: {str(e)}")

        try:
            email_service.send_match_notification(instance)
        except Exception as e:
            logger.error(f"Match email notification failed: {str(e)}")

# Add to existing signals.py content
@receiver(post_save, sender=Chat)
def handle_new_chat_notification(sender, instance, created, **kwargs):
    """Send notifications and emails when a new chat is created and accepted"""
    if created and (not instance.requires_acceptance or instance.is_accepted):
        try:
            for user in [instance.user1, instance.user2]:
                transaction.on_commit(lambda u=user: create_notification_and_send_push(
                    recipient=u,
                    actor=instance.get_other_user(u),
                    verb='CHAT',
                    target_id=instance.id,
                    title_template="New chat with %s!",
                    body_template="You can now message with %s",
                    push_enabled_field='new_chats_notitication',
                    email_enabled=True,
                    data=json.loads(json.dumps(ChatSerializer(instance, context={'user': u}).data, default=str))
                ))
        except Exception as e:
            logger.error(f"Chat notification failed: {str(e)}")
            
        try:
            email_service.send_chat_notification(
                user=instance.user1,
                other_user=instance.user2,
                # instance.get_other_user(user),
                chat=instance
            )
        except Exception as e:
            logger.error(f"Chat email notification failed for {user}: {str(e)}")

@receiver(post_save, sender=MessageRequest)
def handle_message_request(sender, instance, created, **kwargs):
    """Handle notifications for new and accepted message requests"""
    if created:
        # Send websocket notification to both users when request is created
        try:
            for user in [instance.sender, instance.receiver]:
                transaction.on_commit(lambda u=user: create_notification_and_send_push(
                    recipient=u,
                    actor=instance.receiver if u == instance.sender else instance.sender,
                    verb='NEW_REQUEST',
                    target_id=instance.id,
                    title_template="New message request from %s!",
                    body_template="Someone wants to chat with you",
                    push_enabled_field='new_messages_request_notitication',
                    email_enabled=True,
                    data=json.loads(json.dumps(MessageRequestSerializer(instance, context={'user': u}).data, default=str))
                ))
        except Exception as e:
            logger.error(f"Message request websocket notification failed: {str(e)}")
    
    elif instance.status == 'ACCEPTED':
        # Handle notifications for accepted requests
        try:
            for user in [instance.sender, instance.receiver]:
                transaction.on_commit(lambda u=user: create_notification_and_send_push(
                    recipient=u,
                    actor=instance.receiver if u == instance.sender else instance.sender,
                    verb='REQUEST_ACCEPTED',
                    target_id=instance.id,
                    title_template="Chat accepted with %s!",
                    body_template="Your message request was accepted",
                    push_enabled_field='new_messages_notitication',
                    email_enabled=True,
                    data=json.loads(json.dumps(MessageRequestSerializer(instance, context={'user': u}).data, default=str))
                ))
        except Exception as e:
            logger.error(f"Message request notification failed: {str(e)}")
            
        try:
            email_service.send_request_accepted_notification(
                user=instance.receiver,
                other_user=instance.sender,
                request=instance
            )
        except Exception as e:
            logger.error(f"Request acceptance email failed for {instance.receiver}: {str(e)}")


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
                push_enabled_field='new_messages_notitication',
                data=MiniMessageSerializer(instance).data
            ))
        except Exception as e:
            logger.error(f"Message notification failed: {str(e)}")




    # """Handle message notifications and emails"""
    # if created:
    #     try:
    #         def _create_notification():
    #             # Create notification
    #             Notification.objects.create(
    #                 recipient=instance.recipient,
    #                 actor=instance.sender,
    #                 verb='MESSAGE',
    #                 target_id=instance.id
    #             )
    #             # Send email notification
    #             email_service.send_message_notification(instance)
                
    #         transaction.on_commit(_create_notification)
            
    #     except Exception as e:
            logger.error(f"Message notification handling failed: {str(e)}", exc_info=True)