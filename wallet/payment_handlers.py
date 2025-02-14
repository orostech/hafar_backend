
import requests
from django.conf import settings
from .models import CoinRate, PaymentTransaction
from django.utils import timezone

class FlutterwaveHandler:
    API_BASE = 'https://api.flutterwave.com/v3'
    
    def __init__(self):
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
    
    def initialize_payment(self, user, naira_amount, coin_package=None):
        current_rate = CoinRate.objects.filter(is_active=True).latest().rate
        # print(f'm2 {current_rate}')
        coins = int(naira_amount * current_rate)
        print(f'm3 {coins}')
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        # print(f'm3 {headers}')
        payload = {
            'tx_ref': f"HAFAR-COINS-{user.id}-{timezone.now().timestamp()}",
            'amount': str(naira_amount),
            'currency': 'NGN',
            'redirect_url': f"{settings.FRONTEND_URL}/payment-callback",
            'customer': {
                'email': user.email,
                'name': user.profile.display_name
            },
            'customizations': {
                'title': "Hafar Social Coins Purchase",
                'description': f"Purchase of {coins} coins"
            }
        }
        # print(f'm4 {payload}')
        response = requests.post(
            f"{self.API_BASE}/payments",
            json=payload,
            headers=headers
        )
        print(response.json())
        if response.status_code == 200:
            data = response.json()
            try:
                PaymentTransaction.objects.create(
                    user=user,
                    naira_amount=naira_amount,
                    coins=coins,
                    exchange_rate=current_rate,
                    payment_gateway='FLUTTERWAVE',
                    status='PENDING',
                    reference=payload['tx_ref']
                    # data['data']['tx_ref']
                )
                return data['data']['link']
            except Exception as e:
                print(f'Error creating payment transaction: {e}')
        # print(response.json())
        raise Exception("Payment initialization failed")
    
    def verify_payment(self, tx_ref):
        headers = {'Authorization': f'Bearer {self.secret_key}'}
        response = requests.get(
            f"{self.API_BASE}/transactions/verify_by_reference?tx_ref={tx_ref}",
            headers=headers
        )
        if response.status_code == 200:
            return response.json()['data']
        raise Exception("Payment verification failed")