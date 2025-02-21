from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chat')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'message-requests', views.MessageRequestViewSet, basename='message_request')

urlpatterns = [
    path('', include(router.urls)),
    path('send-initial-message/', views.SendInitialMessageView.as_view(), name='send_initial_message'),
    path('messages/search/', views.MessageSearchView.as_view(), name='message_search'),
    path('upload/media/', views.MediaUploadView.as_view(), name='media_upload'),
]