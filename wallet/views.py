from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import (
    Wallet, 
    PaymentTransaction,
    WithdrawalRequest,
    CoinRate
)
from .payment_handlers import FlutterwaveHandler
from .serializers import (
    WalletSerializer,
    PaymentTransactionSerializer,
    WithdrawalRequestSerializer,
    DepositSerializer,
    WithdrawalSerializer,
    CoinRateSerializer
)

class WalletDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            # transactions = PaymentTransaction.objects.filter(
            #     user=request.user
            # ).order_by('-created_at')[:10]

            # withdrawal_requests = WithdrawalRequest.objects.filter(
            #     user=request.user
            # ).order_by('-created_at')[:10]

            current_rate = CoinRate.objects.filter(
                is_active=True
            ).latest('created_at')

            data = {
                'wallet': WalletSerializer(wallet).data,
                # 'transactions': PaymentTransactionSerializer(transactions, many=True).data,
                # 'withdrawal_requests': WithdrawalRequestSerializer(withdrawal_requests, many=True).data,
                'current_rate': CoinRateSerializer(current_rate).data,
                'fee_percentage': 15  # Default withdrawal fee
            }
            return Response(data, status=status.HTTP_200_OK)
            
        except CoinRate.DoesNotExist:
            return Response(
                {'error': 'No active coin rate found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        wallet = request.user.wallet
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)
class CoinRateAPI(APIView):
    def get(self, request):
        rate = CoinRate.objects.filter(is_active=True).last()
        serializer = CoinRateSerializer(rate)
        return Response(serializer.data)