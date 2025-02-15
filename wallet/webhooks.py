from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from wallet.payment_handlers import FlutterwaveHandler
from .models import PaymentTransaction
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

# https://joinhafar.com/payment-callback?status=successful&tx_ref=HAFAR-COINS-f8ba62de-5a55-4d37-b925-9a3a7c30be56-1739595751.705464&transaction_id=8388562

# payload = {'id': 8388867, 
#            'txRef': 'HAFAR-COINS-f8ba62de-5a55-4d37-b925-9a3a7c30be56-1739609066.961968', 
#            'flwRef': 'FLW-MOCK-6506a9268df32556f9ee85d39442b48d', 
#            'orderRef': 'URF_1739609266721_6054435', 'paymentPlan': None, 'paymentPage': None, 'createdAt': '2025-02-15T08:47:47.000Z', 'amount': 3000, 
#            'charged_amount': 3000, 'status': 'successful', 'IP': '54.75.161.64', 'currency': 'NGN', 
#            'appfee': 42, 'merchantfee': 0, 'merchantbearsfee': 1, 'charge_type': 'normal', 
#            'customer': {'id': 2588648, 'phone': None, 'fullName': 'Shooter ', 'customertoken': None, 'email': 'mabsshooter@gmail.com', 
#                         'createdAt': '2025-02-15T08:47:46.000Z', 'updatedAt': '2025-02-15T08:47:46.000Z', 'deletedAt': None, 'AccountId': 2580088}, 
#             'entity': {'card6': '553188', 'card_last4': '2950', 'card_country_iso': 'NG', 'createdAt': '2020-04-24T15:19:22.000Z'}, 'event.type': 'CARD_TRANSACTION'}

@api_view(['POST'])
def flutterwave_webhook(request):
    # Print the incoming payload for debugging
    # print("Webhook Payload:", request.data)
    
    if request.method == 'POST':
        try:
            payload = request.data  # Use request.data instead of request.json()
            tx_ref = payload.get('txRef')
            status = payload.get('status')
            print('pr 1')
            if not tx_ref:
                return Response({'status': 'invalid data'}, status=400)
            
            with transaction.atomic():
                payment = PaymentTransaction.objects.select_for_update().get(reference=tx_ref)
                if status == 'successful':
                    # Verify payment with Flutterwave
                    handler = FlutterwaveHandler()
                    verification = handler.verify_payment(tx_ref)
                    if verification['status'] == 'success':
                        payment.status = 'COMPLETED'
                        payment.user.wallet.add_coins(payment.coins)
                        payment.save()
                        return JsonResponse({'status': 'success'})
                
                # If payment failed or verification failed
                payment.status = 'FAILED'
                payment.save()
                return JsonResponse({'status': 'failed'})
                
        except PaymentTransaction.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
        except Exception as e:
            # Log the error for debugging
            # print("Webhook Error:", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'invalid method'}, status=405)