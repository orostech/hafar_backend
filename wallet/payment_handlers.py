from datetime import timezone
import requests
from django.conf import settings
from .models import CoinRate, PaymentTransaction

class FlutterwaveHandler:
    API_BASE = 'https://api.flutterwave.com/v3'
    
    def __init__(self):
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
    
    def initialize_payment(self, user, naira_amount, coin_package=None):
        current_rate = CoinRate.objects.filter(is_active=True).latest().rate
        coins = int(naira_amount * current_rate)
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        payload = {
            'tx_ref': f"HAFAR-COINS-{user.id}-{timezone.now().timestamp()}",
            'amount': str(naira_amount),
            'currency': 'NGN',
            'redirect_url': f"{settings.FRONTEND_URL}/payment-callback",
            'customer': {
                'email': user.email,
                'name': user.get_full_name()
            },
            'customizations': {
                'title': "Hafar Social Coins Purchase",
                'description': f"Purchase of {coins} coins"
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
                naira_amount=naira_amount,
                coins=coins,
                exchange_rate=current_rate,
                payment_gateway='FLUTTERWAVE',
                status='PENDING',
                reference=data['data']['tx_ref']
            )
            return data['data']['link']
        raise Exception("Payment initialization failed")