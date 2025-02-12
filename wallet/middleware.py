from wallet.models import Transaction


class CoinMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track Super Like costs
        if request.path == '/api/likes/' and request.method == 'POST':
            if request.data.get('like_type') == 'SUPER':
                user = request.user
                if user.wallet.deduct_coins(10):
                    Transaction.objects.create(
                        user=user,
                        amount=-10,
                        transaction_type='SPEND',
                        description='Super Like'
                    )
        
        # Track message request costs
        if request.path.startswith('/api/messages/') and request.method == 'POST':
            if request.data.get('is_paid'):
                user = request.user
                if user.wallet.deduct_coins(10):
                    Transaction.objects.create(
                        user=user,
                        amount=-10,
                        transaction_type='SPEND',
                        description='Paid Message'
                    )
        
        return response