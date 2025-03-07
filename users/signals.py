from django.db.models.signals import post_save
from django.dispatch import receiver
from notification.email_service import EmailService
from wallet.models import Wallet
from .models import User, Profile, UserPhoto  # Adjust according to your actual app structure

email_service = EmailService()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
                user=instance,
                display_name=instance.username)
        Wallet.objects.create(user=instance)
      

@receiver(post_save, sender=Profile)
@receiver(post_save, sender=Profile)
def check_profile_completion_on_profile_update(sender, instance, created, **kwargs):
    required_fields = [
        instance.display_name != 'Unknown',  # Default value check
        instance.date_of_birth is not None,
        instance.gender,
        instance.user.photos.exists()  # Check if photos exist
    ]
    
    if all(required_fields):
        # Change user status to 'PA' and send welcome email if not already sent
        if not instance.welcome_email_sent:
            try:
                email_service.send_welcome_email(instance.user)
                # Use update to avoid recursion
                Profile.objects.filter(pk=instance.pk).update(welcome_email_sent=True, user_status='PA')
            except Exception as e:
                print(f"Error sending welcome email: {e}")
        else:
            # If the email has been sent, just update the user status
            Profile.objects.filter(pk=instance.pk).update(user_status='PA')

@receiver(post_save, sender=UserPhoto)
def check_profile_completion_on_photo_upload(sender, instance, created, **kwargs):
    if created:
        profile = instance.user.profile
        required_fields = [ 
            profile.display_name != 'Unknown',
            profile.date_of_birth is not None,
            profile.gender,
            instance.user.photos.exists()  
        ]
        
        if all(required_fields):
            # Change user status to 'PA' and send welcome email if not already sent
            if not profile.welcome_email_sent:
                try:
                    email_service.send_welcome_email(instance.user)
                    Profile.objects.filter(pk=profile.pk).update(welcome_email_sent=True, user_status='PA')
                except Exception as e:
                    print(f"Error sending welcome email: {e}")
            else:
                # If the email has been sent, just update the user status
                Profile.objects.filter(pk=profile.pk).update(user_status='PA')