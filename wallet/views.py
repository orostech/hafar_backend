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
class DepositAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer = DepositSerializer()
    
# {"amount":"3000"}
    def post(self, request):
        print('m011')
        serializer = DepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print('m01')
            current_rate = CoinRate.objects.filter(is_active=True).latest('created_at')
            naira_amount = serializer.validated_data['amount']
            print('m1')
            coins = int(naira_amount * current_rate.rate)
            handler = FlutterwaveHandler()
            print('m2')
            payment_url = handler.initialize_payment(
                user=request.user,
                naira_amount=naira_amount
            )
            print('m3')
            return Response({'payment_url': payment_url})
        except Exception as e:
            print(str(e))
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
class WithdrawalAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coins_amount = serializer.validated_data['coins_amount']
            wallet = request.user.wallet
            
            if wallet.balance < coins_amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process withdrawal
            current_rate = CoinRate.objects.filter(is_active=True).latest('created_at')
            fee_percentage = 5  # Could be configurable
            fee = (coins_amount * fee_percentage) // 100
            total_deduction = coins_amount + fee
            
            with transaction.atomic():
                wallet.withdraw_coins(total_deduction)
                withdrawal = WithdrawalRequest.objects.create(
                    user=request.user,
                    coins_amount=coins_amount,
                    exchange_rate=current_rate.rate,
                    naira_amount=(coins_amount - fee) / current_rate.rate,
                    fee_percentage=fee_percentage,
                    status='PENDING'
                )
            
            serializer = WithdrawalRequestSerializer(withdrawal)
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class TransactionHistoryAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = PaymentTransaction.objects.filter(user=request.user)
        serializer = PaymentTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class WithdrawalHistoryAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        withdrawals = WithdrawalRequest.objects.filter(user=request.user)
        serializer = WithdrawalRequestSerializer(withdrawals, many=True)
        return Response(serializer.data)