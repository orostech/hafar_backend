from django.contrib import admin
from .models import (
    CoinRate,
    Wallet,
    Transaction,
    WithdrawalRequest,
    PaymentTransaction,
    Referral,
)


@admin.register(CoinRate)
class CoinRateAdmin(admin.ModelAdmin):
    list_display = ('rate', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('rate',)
    ordering = ('-created_at',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'total_earned', 'total_spent', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')  # Assuming User model has username and email
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'timestamp', 'description')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'description')
    ordering = ('-timestamp',)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins_amount', 'naira_amount', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'naira_amount', 'coins', 'payment_gateway', 'status', 'reference', 'created_at')
    list_filter = ('status', 'payment_gateway', 'created_at')
    search_fields = ('user__username', 'user__email', 'reference')
    ordering = ('-created_at',)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'coins_earned', 'created_at')
    search_fields = ('referrer__username', 'referred_user__username', 'referrer__email', 'referred_user__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
