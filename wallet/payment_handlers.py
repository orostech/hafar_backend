
import requests
from django.conf import settings
from .models import CoinRate, PaymentTransaction
from django.utils import timezone
# PIN authentication	Mastercard	5531886652142950	09/32	564	12345	3310
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
                'name': user.profile.display_name
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
        # {'status': 'success', 'message': 'Transaction fetched successfully', 'data': {'id': 8388867, 'tx_ref': 'HAFAR-COINS-f8ba62de-5a55-4d37-b925-9a3a7c30be56-1739609066.961968', 
        # 'flw_ref': 'FLW-MOCK-6506a9268df32556f9ee85d39442b48d', 'device_fingerprint': 'N/A', 'amount': 3000, 'currency': 'NGN', 'charged_amount': 3000, 'app_fee': 42, 'merchant_fee': 0, 
        # 'processor_response': 'successful', 'auth_model': 'PIN', 'ip': '54.75.161.64', 'narration': 'CARD Transaction ', 'status': 'successful', 'payment_type': 'card', 
        # 'created_at': '2025-02-15T08:47:47.000Z', 'account_id': 2580088, 'card': {'first_6digits': '553188', 'last_4digits': '2950', 'issuer': ' CREDIT',
        #  'country': 'NIGERIA NG', 'type': 'MASTERCARD', 'token': 'flw-t1nf-d46c7ecffa7d12c492c891418e8fdd4e-m03k', 'expiry': '09/32'}, 
        # 'meta': {'__CheckoutInitAddress': 'https://checkout-v2.dev-flutterwave.com/v3/hosted/pay'}, 'amount_settled': 2954.85, 'customer': {'id': 2588648, 'name': 'Shooter ', 'phone_number': 
        # 'N/A', 'email': 'mabsshooter@gmail.com', 'created_at': '2025-02-15T08:47:46.000Z'}}}
        # print(response.json())
        if response.status_code == 200:
            return response.json()
        # ['data']
        raise Exception("Payment verification failed")

        
        
# https://checkout-v2.dev-flutterwave.com/v3//hosted/pay/dc8db8814bbf7a8f19a6