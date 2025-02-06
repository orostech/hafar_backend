import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hafar_backend.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from .middleware import JwtAuthMiddleware
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})


# import os

# from django.core.asgi import get_asgi_application
# import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# # from channels.auth import AuthMiddlewareStack
# from chat.routing import websocket_urlpatterns
# from .middleware import JwtAuthMiddleware

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hafar_backend.settings')

# # application = get_asgi_application()


# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": JwtAuthMiddleware(
#         URLRouter(websocket_urlpatterns)
#     ),
# })