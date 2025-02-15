from decimal import Decimal
from rest_framework import serializers
from .models import (
    Wallet, 
    PaymentTransaction,
    WithdrawalRequest,
    CoinRate
)



class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance', 'total_earned', 'total_spent']
        read_only_fields = fields

class CoinRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinRate
        fields = ['rate', 'created_at']
        read_only_fields = fields

class PaymentTransactionSerializer(serializers.ModelSerializer):
    naira_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        # min_value=Decimal('0.00')
    )
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'naira_amount', 'coins', 
            'exchange_rate', 'status', 'created_at'
        ]
        read_only_fields = fields

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    naira_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
    #    min_value=Decimal('0.00')
    )
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'coins_amount', 'naira_amount',
            'fee_percentage', 'status', 'created_at'
        ]
        read_only_fields = fields

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('100.00')
        # min_value=100.00
    )
    

class WithdrawalSerializer(serializers.Serializer):
    coins_amount = serializers.IntegerField(min_value=1000)