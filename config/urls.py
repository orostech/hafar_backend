from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfigurationViewSet

router = DefaultRouter()
router.register(r'config', ConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]