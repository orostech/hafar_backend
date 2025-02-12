from datetime import timezone
from django.db import models
from django.conf import settings

class PremiumSubscription(models.Model):
    TIERS = [
        ('BASIC', 'Basic'),
        ('VIP', 'VIP'),
        ('PREMIUM', 'Premium'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tier = models.CharField(max_length=10, choices=TIERS)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    coin_cost = models.PositiveIntegerField()

    @property
    def remaining_days(self):
        return (self.end_date - timezone.now()).days

    def renew(self, coins):
        if coins >= self.coin_cost:
            self.end_date += timezone.timedelta(days=30)
            self.save()
            return True
        return False