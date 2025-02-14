# wallet/urls.py
from django.urls import path

from .webhooks import flutterwave_webhook
from .views import (
    WalletAPI,
    DepositAPIView,
    WithdrawalAPI,
    TransactionHistoryAPI,
    WithdrawalHistoryAPI,
    CoinRateAPI,
)

urlpatterns = [
    path('wallet/', WalletAPI.as_view(), name='wallet-detail'),
    path('wallet/coin-rate/', CoinRateAPI.as_view(), name='coin-rate'),
    path('wallet/deposit/', DepositAPIView.as_view(), name='deposit'),
    path('wallet/withdraw/', WithdrawalAPI.as_view(), name='withdraw'),
    path('wallet/transactions/', TransactionHistoryAPI.as_view(), name='transaction-history'),
    path('wallet/withdrawals/', WithdrawalHistoryAPI.as_view(), name='withdrawal-history'),
    path('webhooks/flutterwave/', flutterwave_webhook, name='flutterwave-webhook'),
]