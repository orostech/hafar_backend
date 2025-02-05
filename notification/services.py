# notifications/services.py
from django.core.mail import send_mail
from django.conf import settings
from pyfcm import FCMNotification

def send_match_email(user, matched_user):
    subject = 'New Match!'
    message = f'You matched with {matched_user.username}!'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])




def send_fcm_notification(user, message):
    push_service = FCMNotification(api_key=settings.FCM_API_KEY)
    registration_id = user.fcm_token  # Store FCM tokens in the User model
    result = push_service.notify_single_device(
        registration_id=registration_id,
        message_title='New Notification',
        message_body=message
    )
    return result