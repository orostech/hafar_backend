from django.urls import re_path
from users.consumers import UserActivityConsumer
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path("ws/user_activity/", UserActivityConsumer.as_asgi()),
]