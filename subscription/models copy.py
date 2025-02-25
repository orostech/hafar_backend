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
    coin_price = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField()
    description = models.TextField( null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    iap_apple_id = models.CharField(max_length=100, blank=True, null=True)  # Apple Product ID
    iap_google_id = models.CharField(max_length=100, blank=True, null=True)  # Google Product ID
    is_consumable = models.BooleanField(default=False)

    class Meta:
        ordering = ['coin_price']

    def __str__(self):
        return f"{self.get_name_display()} Plan - {self.coin_price} coins"

class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
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
    

class IAPReceipt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10, choices=[('APPLE', 'iOS'), ('GOOGLE', 'Android')])
    product_id = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=255, unique=True)
    purchase_token = models.TextField()  # For Google
    receipt_data = models.TextField()    # For Apple
    verified = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True)

# from iap.verification import verify_apple_receipt, verify_google_purchase

# class IAPViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]

#     @action(detail=False, methods=['post'])
#     def verify(self, request):
#         platform = request.data.get('platform')
#         receipt = request.data.get('receipt')
#         product_id = request.data.get('product_id')
        
#         try:
#             if platform == 'APPLE':
#                 verification = verify_apple_receipt(receipt)
#             elif platform == 'GOOGLE':
#                 verification = verify_google_purchase(
#                     receipt['purchaseToken'],
#                     receipt['productId'],
#                     receipt['packageName']
#                 )
#             else:
#                 return Response({'error': 'Invalid platform'}, status=400)

#             if verification['valid']:
#                 # Handle subscription activation
#                 plan = SubscriptionPlan.objects.get(iap_apple_id=product_id) if platform == 'APPLE' \
#                     else SubscriptionPlan.objects.get(iap_google_id=product_id)
                
#                 UserSubscription.objects.create(
#                     user=request.user,
#                     plan=plan,
#                     start_date=timezone.now(),
#                     end_date=verification['expiry_date'],
#                     is_active=True
#                 )
                
#                 return Response({'status': 'Subscription activated'}, status=200)
#             return Response({'error': 'Invalid receipt'}, status=400)
            
#         except SubscriptionPlan.DoesNotExist:
#             return Response({'error': 'Product not found'}, status=404)