# # wallet/models.py
# from django.db import models
# from django.conf import settings
# from django.utils import timezone
# from django.db.models import F

# class Wallet(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL, 
#         on_delete=models.CASCADE, 
#         related_name='wallet'
#     )
#     balance = models.PositiveIntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def deduct_coins(self, amount):
#         if self.balance >= amount:
#             self.balance = F('balance') - amount
#             self.save(update_fields=['balance'])
#             return True
#         return False

#     def add_coins(self, amount):
#         self.balance = F('balance') + amount
#         self.save(update_fields=['balance'])
#         return True

# class Transaction(models.Model):
#     TRANSACTION_TYPES = [
#         ('PURCHASE', 'Coin Purchase'),
#         ('EARN', 'Earned Coins'),
#         ('SPEND', 'Spent Coins'),
#         ('TRANSFER', 'Peer Transfer'),
#         ('WITHDRAWAL', 'Withdrawal'),
#         ('REFERRAL', 'Referral Bonus'),
#     ]

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     amount = models.IntegerField()
#     transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
#     description = models.CharField(max_length=255)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     related_object_id = models.PositiveIntegerField(null=True, blank=True)

#     class Meta:
#         ordering = ['-timestamp']

# class WithdrawalRequest(models.Model):
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('APPROVED', 'Approved'),
#         ('REJECTED', 'Rejected'),
#     ]

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     amount = models.PositiveIntegerField()
#     fee = models.PositiveIntegerField()
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     created_at = models.DateTimeField(auto_now_add=True)
#     processed_at = models.DateTimeField(null=True, blank=True)

# class PaymentTransaction(models.Model):
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('COMPLETED', 'Completed'),
#         ('FAILED', 'Failed'),
#     ]

#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     coins = models.PositiveIntegerField()
#     payment_gateway = models.CharField(max_length=50)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     reference = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)

# class Referral(models.Model):
#     referrer = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='referrals_made'
#     )
#     referred_user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='referral'
#     )
#     coins_earned = models.PositiveIntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)