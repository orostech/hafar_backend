from rest_framework.throttling import SimpleRateThrottle

class MessageRateThrottle(SimpleRateThrottle):
    scope = 'message'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'message_throttle_{request.user.id}'
        return None
    
    def get_rate(self):
        return '10/minute'