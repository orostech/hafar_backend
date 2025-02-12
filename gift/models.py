from django.db import models
from django.conf import settings

class VirtualGift(models.Model):
    GIFT_TYPES = [
        ('ROSE', 'Virtual Rose'),
        ('CHOCOLATE', 'Chocolate Box'),
        ('DIAMOND', 'Diamond'),
    ]
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_gifts', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_gifts', on_delete=models.CASCADE)
    gift_type = models.CharField(max_length=10, choices=GIFT_TYPES)
    message = models.TextField(blank=True)
    coins_value = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Deduct coins when sending gift"""
        if not self.pk:  # Only on creation
            if self.sender.wallet.balance >= self.coins_value:
                super().save(*args, **kwargs)
                self.sender.wallet.deduct_coins(self.coins_value)
                # Add 70% of value to receiver's wallet (platform keeps 30%)
                self.receiver.wallet.add_coins(int(self.coins_value * 0.7))
            else:
                raise ValueError("Insufficient coins to send gift")
        else:
            super().save(*args, **kwargs)