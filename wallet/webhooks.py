from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from wallet.payment_handlers import FlutterwaveHandler
from .models import PaymentTransaction
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def flutterwave_webhook(request):
    if request.method == 'POST':
            try:
                payload = request.json()
                tx_ref = payload.get('data', {}).get('tx_ref')
                status = payload.get('data', {}).get('status')
                print(request.data)
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
                    
                    payment.status = 'FAILED'
                    payment.save()
                    return JsonResponse({'status': 'failed'})
                    
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)  
    return JsonResponse({'status': 'invalid method'}, status=405)
    # # @csrf_exempt
    # @api_view(['POST'])
    # def flutterwave_webhook(request):
    #     if request.method == 'POST':
    #         payload = request.POST
    #         # Verify payload with Flutterwave
    #         tx_ref = payload.get('tx_ref')
    #         transaction = PaymentTransaction.objects.get(reference=tx_ref)
            
    #         if payload['status'] == 'successful':
    #             transaction.status = 'COMPLETED'
    #             transaction.user.wallet.add_coins(transaction.coins)
    #             transaction.save()
    #             return JsonResponse({'status': 'success'})
            
    #         transaction.status = 'FAILED'
    #         transaction.save()
    #         return JsonResponse({'status': 'failed'})
    #     return JsonResponse({'status': 'invalid method'}, status=400)