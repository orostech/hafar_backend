from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
import logging
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(token):
    try:
        access_token = AccessToken(token)
        user_id= access_token['user_id']
        user = User.objects.get(id=user_id)
        print(user)
        return user
    except Exception as e:
        logger.error(f"Failed to authenticate user: {e}")
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())  
        # print(query_string)
        # print('query_string')
        token = query_string.get("token", [None])[0]
        scope["user"] = await get_user(token)
        return await super().__call__(scope, receive, send)
       

def JwtAuthMiddlewareStack(inner):
    return  JwtAuthMiddleware(inner)
