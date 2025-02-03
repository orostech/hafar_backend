from celery import shared_task
from django.utils import timezone
from .models import Message, Chat
from django.db.models import Q

@shared_task
def expire_temporary_messages():
    Message.objects.filter(
        expires_at__lte=timezone.now()
    ).delete()

@shared_task
def clean_old_chats():
    # Archive chats inactive for 30 days
    cutoff = timezone.now() - timedelta(days=30)
    Chat.objects.filter(
        last_activity__lte=cutoff,
        is_active=True
    ).update(is_active=False)

@shared_task
def send_push_notifications():
    pass
    # from firebase_admin import messaging
    # # Get unread messages
    # unread_messages = Message.objects.filter(
    #     read_at__isnull=True,
    #     created_at__gte=timezone.now() - timedelta(hours=1)
    # )
    
    # for message in unread_messages:
    #     user = message.chat.get_other_user(message.sender)
    #     if user.device_token:
    #         notification = messaging.Notification(
    #             title=f'New message from {message.sender.profile.display_name}',
    #             body=message.content[:100]
    #         )
    #         messaging.send(messaging.Message(
    #             notification=notification,
    #             token=user.device_token
    #         ))