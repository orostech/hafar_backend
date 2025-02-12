from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Wallet, Referral
from django.conf import settings
from match.models import SwipeLimit
from users.models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    """Create wallet when new user registers"""
    if created:
        Wallet.objects.create(user=instance)

@receiver(post_save, sender=Referral)
def award_referral_bonus(sender, instance, created, **kwargs):
    """Award coins when referral is completed"""
    if created:
        referrer_wallet = instance.referrer.wallet
        referrer_wallet.add_coins(instance.coins_earned)
        referrer_wallet.save()

@receiver(post_save, sender=Profile)
def award_profile_completion_coins(sender, instance, created, **kwargs):
    """Award 5 coins when profile is completed"""
    completeness_threshold = 0.8
    if instance.completeness_score >= completeness_threshold:
        wallet = instance.user.wallet
        if not instance.completion_coins_awarded:
            wallet.add_coins(5)
            instance.completion_coins_awarded = True
            instance.save()