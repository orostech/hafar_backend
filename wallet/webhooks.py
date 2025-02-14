from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PaymentTransaction

@csrf_exempt
def flutterwave_webhook(request):
    if request.method == 'POST':
        payload = request.POST
        # Verify payload with Flutterwave
        tx_ref = payload.get('tx_ref')
        transaction = PaymentTransaction.objects.get(reference=tx_ref)
        
        if payload['status'] == 'successful':
            transaction.status = 'COMPLETED'
            transaction.user.wallet.add_coins(transaction.coins)
            transaction.save()
            return JsonResponse({'status': 'success'})
        
        transaction.status = 'FAILED'
        transaction.save()
        return JsonResponse({'status': 'failed'})
    return JsonResponse({'status': 'invalid method'}, status=400)