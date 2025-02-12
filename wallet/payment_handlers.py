from datetime import timezone
import requests
from django.conf import settings
from .models import PaymentTransaction

class FlutterwaveHandler:
    API_BASE = 'https://api.flutterwave.com/v3'
    
    def __init__(self):
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
    
    def initialize_payment(self, user, amount, coin_package):
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        payload = {
            'tx_ref': f"HAFAR-COINS-{user.id}-{timezone.now().timestamp()}",
            'amount': str(amount),
            'currency': 'NGN',
            'redirect_url': f"{settings.FRONTEND_URL}/payment-callback",
            'customer': {
                'email': user.email,
                'name': user.get_full_name()
            },
            'customizations': {
                'title': "Hafar Social Coins Purchase",
                'description': f"Purchase of {coin_package} coins"
            }
        }
        
        response = requests.post(
            f"{self.API_BASE}/payments",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            PaymentTransaction.objects.create(
                user=user,
                amount=amount,
                coins=coin_package,
                payment_gateway='FLUTTERWAVE',
                status='PENDING',
                reference=data['data']['tx_ref']
            )
            return data['data']['link']
        raise Exception("Payment initialization failed")