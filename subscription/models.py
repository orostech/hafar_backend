from django.db import models
from django.conf import settings
from django.utils import timezone

class SubscriptionPlan(models.Model):
    TIER_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('MONTH', 'Monthly'),
        ('THREEMONTH', '3 Month'),
    ]
    
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    title = models.CharField(max_length=30, blank=True,)

    coin_price = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField()
    description = models.TextField( null=True, blank=True)
    iap_apple_id = models.CharField(max_length=100, blank=True, null=True)  # Apple Product ID
    iap_google_id = models.CharField(max_length=100, blank=True, null=True)  # Google Product ID
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['coin_price']

    def __str__(self):
        return f"{self.get_name_display()} Plan - {self.coin_price} coins"

class UserSubscription(models.Model):
    PURCHASE_METHODS = [
        ('COINS', 'Coins'),
        ('PLAY_STORE', 'Play Store'),
        ('APP_STORE', 'App Store'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    purchase_method = models.CharField(max_length=20, choices=PURCHASE_METHODS, default='COINS')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
         # Ensure start_date is set to the current time if it's None
        if not self.start_date:
            self.start_date = timezone.now()

          # Calculate end_date based on start_date and plan duration
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} Subscription"