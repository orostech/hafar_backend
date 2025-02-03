# chat/middleware.py
from datetime import time
import logging
from django.core.cache import cache
from rest_framework.exceptions import Throttled
logger = logging.getLogger(__name__)

class MessageRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.limits = {
            'message': (10, 60),  # 10 messages/minute
            'media': (3, 60)
        }

    def __call__(self, request):
        user = request.user
        key = f"ratelimit:{user.id}:{request.path}"
        
        current = cache.get(key,
                             0)
        if current >= self.limits[request.path][0]:
            raise Throttled()
            
        cache.incr(key, timeout=self.limits[request.path][1])
        return self.get_response(request)
    

class MonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # Log to monitoring system
        logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.2f}s")
        return response