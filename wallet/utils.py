from decimal import Decimal
from django.db import transaction
from .models import CoinRate, WithdrawalRequest

def process_withdrawal(user, coins_amount):
    try:
        current_rate = CoinRate.objects.filter(is_active=True).latest().rate
        fee_percentage = 15
        with transaction.atomic():
            success = user.wallet.withdraw_coins(coins_amount, fee_percentage)
            if success:
                fee = (coins_amount * fee_percentage)
                naira_amount =  Decimal(coins_amount - fee)
                # TODO ADD THE CHARGE TO OUR OWN DASHBOARD
                WithdrawalRequest.objects.create(
                    user=user,
                    amount=coins_amount,
                    exchange_rate=current_rate,
                    naira_amount=naira_amount,
                    fee_percentage=fee_percentage,
                    status='PENDING'
                )
                return True
            return False
    except Exception as e:
        print(e)
        return False