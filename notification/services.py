# notifications/services.py
# from django.core.mail import send_mail
from django.conf import settings
# from pyfcm import FCMNotification
import firebase_admin
from firebase_admin import messaging
from pathlib import Path


# serviceAccountKey = Path(__file__).resolve().parent.parent / "settings" / "serviceAccountKey.json"


class FirebaseNotificationService:
    @classmethod
    def initialize(cls):
        if not firebase_admin._apps:
            cred = firebase_admin.credentials.Certificate(
                # serviceAccountKey
                'notification/serviceAccountKey.json'
            )
            firebase_admin.initialize_app(cred)

    @classmethod
    def send_push_notification(cls, recipient, title, body, data=None):
        cls.initialize()
        if not recipient.device_token:
            return
        
        if data:
             data = {str(k): str(v) for k, v in data.items()}
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=recipient.device_token,
        )

        try:
            messaging.send(message)
        except Exception as e:
            # Implement proper error logging
            pass

# def send_match_email(user, matched_user):
#     subject = 'New Match!'
#     message = f'You matched with {matched_user.username}!'
#     send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])




# def send_fcm_notification(user, message):
#     push_service = FCMNotification(api_key=settings.FCM_API_KEY)
#     registration_id = user.fcm_token  # Store FCM tokens in the User model
#     result = push_service.notify_single_device(
#         registration_id=registration_id,
#         message_title='New Notification',
#         message_body=message
#     )
#     return result

