# urls.py (gift app)
from django.urls import path
from .views import GiftShopAPI, SendGiftAPI, GiftHistoryAPI

urlpatterns = [
    # Endpoint to list all available gifts
    path('shop/', GiftShopAPI.as_view(), name='gift_shop'),
    
    # Endpoint to send a gift
    path('send/', SendGiftAPI.as_view(), name='send_gift'),
    
    # Endpoint to retrieve gift history for the authenticated user
    path('history/', GiftHistoryAPI.as_view(), name='gift_history'),
]