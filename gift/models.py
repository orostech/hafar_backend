from django.db import models
from django.conf import settings
from django.db import transaction

from wallet.models import Transaction, Wallet


class GiftType(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=50, unique=True)
    coin_price = models.PositiveIntegerField()
    image = models.ImageField(upload_to='gifts/images/')
    animation = models.FileField(
        upload_to='gifts/animations/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['coin_price']
        indexes = [
            models.Index(fields=['key', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.coin_price} coins)"


class VirtualGift(models.Model):
    # GIFT_TYPES = [
    #     ('ROSE', 'Rose'),
    #     ('HEART', 'Heart'),
    #     ('CAKE', 'Cake'),
    #     ('GIFT_BOX', 'Gift Box'),
    #     ('DIAMOND', 'Diamond'),
    #     ('CROWN', 'Crown'),
    #     ('BALLOON', 'Balloon'),
    #     ('TROPHY', 'Trophy'),
    #     ('ROCKET', 'Rocket'),
    #     ('CAR', 'Car'),
    # ]

    # GIFT_PRICES = {
    #     'ROSE': 10,
    #     'HEART': 15,
    #     'CAKE': 30,
    #     'GIFT_BOX': 60,
    #     'DIAMOND': 120,
    #     'CROWN': 250,
    #     'BALLOON': 500,
    #     'TROPHY': 1000,
    #     'ROCKET': 2000,
    #     'CAR': 4000,
    # }

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_gifts', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_gifts',  on_delete=models.CASCADE)
    gift_type = models.ForeignKey(GiftType,on_delete=models.PROTECT, related_name='gifts')
    message = models.TextField(blank=True)
    coins_value = models.PositiveIntegerField(editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['timestamp']),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            if not self.gift_type.is_active:
                raise ValueError("This gift type is not available")

            self.coins_value = self.gift_type.coin_price
            if self.coins_value == 0:
                raise ValueError("Invalid gift type")

            with transaction.atomic():
                # Lock sender's wallet to prevent race conditions
                sender_wallet = Wallet.objects.select_for_update().get(user=self.sender)
                if sender_wallet.balance < self.coins_value:
                    raise ValueError("Insufficient coins to send gift")

                super().save(*args, **kwargs)

                # Deduct coins from sender
                sender_wallet.deduct_coins(self.coins_value)
                # TODO PLATF ADD
                # Add 90% to receiver's wallet (platform keeps 10%)
                receiver_coins = int(self.coins_value * 0.9)
                self.receiver.wallet.add_coins(receiver_coins)

                # Create transaction records
                Transaction.objects.create(
                    user=self.sender,
                    amount=-self.coins_value,
                    transaction_type='GIFT_SENT',
                    description=f"Sent {self.gift_type.name} to {self.receiver.username}"
                )
                
                Transaction.objects.create(
                    user=self.receiver,
                    amount=receiver_coins,
                    transaction_type='GIFT_RECEIVED',
                    description=f"Received {self.gift_type.name} from {self.sender.username}"
                )

        else:
            super().save(*args, **kwargs)
