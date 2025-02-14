from django.db.models.signals import post_save
from django.dispatch import receiver
from notification.email_service import EmailService
from wallet.models import Wallet
from .models import User, Profile  # Adjust according to your actual app structure

email_service = EmailService()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Wallet.objects.create(user=instance)
        try:
            email_service.send_welcome_email(instance)
        except:
            print("Error sending welcome email")
        

