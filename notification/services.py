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
            #    settings.FIREBASE_CREDENTIALS
                # 'notification/serviceAccountKey.json'
                {
  "type": "service_account",
  "project_id": "hafar-b5749",
  "private_key_id": "e19e380e0ed7bc7bf5da7cd05c349c0abf0ce51a",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDEEPB226kQyL0/\nmRt3CQAALKWRUO1anj3cS6jr+b1m22fyskrddPlzfL+cYVkEM0UYy2FP3q3xBCtR\nh7jPRBeSpS/u/Z7jjRoikaCTO7hN6L8UR1kpWoKv3Z+ORSvUyisoZvF/00NQjGNw\nDffAuHfZSElNkr0EqRoHFoll0gLCVi08v2eyh402X3M7hhxw87j8sMIIiAkVejJM\n59bPk9iSOCCUuDwMdIeKrUOvjuWpCNiNkGkqDmsBmr8Vq5II280r0EzVmIPXTd/n\n7sceaSRGQ3OXpMYgn1ROi28jFRwRqYpoChaOTkh2IBBNrs/7Z+B1eKnazb4ZfkqF\nW6FfAfNFAgMBAAECggEAGL1gckb+WslRo+xAXHFMyDjZ/W+eO5B7EsiTPI9rOEbY\nI3Ye3znK3ikwDl30OwTzI5FKKqdZAG/7vVJoXfLkHJNubHQhL+pWkWUZw2pGM8J6\nFed41zB+DA3le7C7uqJ19qeisnPoawoD5BhHGlDMgqTN5xVsd2GVEK7l0GzC/11i\n0L5jzfstvUYrXYJ0wpP/Gpn80xpM4W9tPSVxFDKqbmKaI3bwWvrxqjFzBpZkYqXx\n887j0N5EEH1rJeGpPjuvadvHqQXTXtwi5qOhFHWzqQXBJkFpaujy7il9oIQkJs4+\nueH8dy3SsodRfH2/I9XpbQ8zxsSJW0Chppf/dwb68QKBgQDmoeN8b0t6EaoA5FCU\nT0PC4AEDkgzF42aomZMo7XlwIJ4kMfgYHK6ZbgPeSlsVFYQBPIS5Jy1P//IG8AyF\nyOJvvwiQPX47u29MbFrWXkmTL8/ObzjcHqzsrdkXz4juoKVfy5Qoqqr1W9f9djHa\nLOhQdL2X3OkSe3JuwTRoO/0fbQKBgQDZob2cR42/k3npaWbmaRT/9BFilEoSdjgL\n43KzX7BMZR/vyLyGIphzGXwtKRoHPstjpyRvFg4CykMFWEHwv21DjxMh2HaFkYmL\nVRzbZxzinzEozYOXR7p4X0F2ZEGQzM6v4K8A4FUFutsOvu6RnIA8R7oZp5M35AKD\nLOhU+2FEOQKBgCm2S9t8kY0RVsr0gDJip6G+O9C2gILl3vJNXFVBpf4GmDN5qiJK\nRbXQNPjmP9TvYEGM/YAzOrnGU7K3hbxImdOWHGliBcut2bJbwo4U3X+2XQI8EW+W\nSLZBtwrcaSqneWF7A1/bhjH8G3NnBhsslhO/GW828Bx8oTSw0tarStt9AoGACMiL\nU4RbxzCXigEUAxaYn1/lV7ouZyJYTrqGRZEGF385U78hRLSevH550YTIJSS2prX3\nNXiJZjltjQir2KCRM1nR5trKpcdi6rmrqXs24jqUjFYHCpL9hqApjzKqpsJtURHb\nXkivhcSt1KGGFWBgmI44h5KI0YelRlAIrG1c1pkCgYBWTjxm0xEVcnyIDpfRUuxb\nzYkC7bNRtTi4uF+GrPTHbyR+NSpA0NzZODn3msCEm+TCA4X+00TB9Qf4wT6iBR6U\nfQLq1eHmDUQo6TRMjJ8bGUeHyD331lZetsXksWXGzOElr1QXXLvgS1/n1Vwx2sQi\npFeuTVJ0wEyqy9MvRUgWBg==\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-uxkpu@hafar-b5749.iam.gserviceaccount.com",
  "client_id": "115539353451589095587",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-uxkpu%40hafar-b5749.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
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

