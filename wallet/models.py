# wallet/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import F

class CoinRate(models.Model):
    rate = models.DecimalField(max_digits=2, decimal_places=2, help_text="Coins per 1 Naira")  # E.g 1 Naira = 10 coins
    # rate = models.PositiveIntegerField(help_text="Coins per 1 Naira")  # E.g 1 Naira = 10 coins
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"1 NGN = {self.rate} coins (Active: {self.is_active})"

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.PositiveIntegerField(default=0)
    total_earned = models.PositiveIntegerField(default=0)
    total_spent = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s wallet: {self.balance} coins"

    class Meta:
        indexes = [models.Index(fields=['user', 'balance'])]


    def deduct_coins(self, amount):
        if self.balance >= amount:
            self.balance = F('balance') - amount
            self.total_spent = F('total_spent') + amount
            self.save(update_fields=['balance', 'total_spent'])
            return True
        return False

    def add_coins(self, amount):
        self.balance = F('balance') + amount
        self.total_earned = F('total_earned') + amount
        self.save(update_fields=['balance', 'total_earned'])
        return True
    
    def withdraw_coins(self, coins_amount, fee_percentage=15):
        fee = (coins_amount * fee_percentage) // 100
        total_deduction = coins_amount + fee
        
        if self.balance >= total_deduction:
            self.balance = F('balance') - total_deduction
            self.total_spent = F('total_spent') + total_deduction
            self.save(update_fields=['balance', 'total_spent'])
            return True
        return False

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Coin Purchase'),
        ('EARN', 'Earned Coins'),
        ('SPEND', 'Spent Coins'),
        ('TRANSFER', 'Peer Transfer'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('REFERRAL', 'Referral Bonus'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exchange_rate = models.PositiveIntegerField()
    coins_amount = models.PositiveIntegerField()
    naira_amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee_percentage = models.PositiveIntegerField(default=5, help_text="Percentage fee for withdrawal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exchange_rate = models.PositiveIntegerField(null=True)
    naira_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coins = models.PositiveIntegerField()
    payment_gateway = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reference = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Referral(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_made'
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral'
    )
    coins_earned = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)