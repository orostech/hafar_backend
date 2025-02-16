from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, UserSubscriptionViewSet

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscription-plans')
router.register(r'subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')

urlpatterns = [
    path('', include(router.urls)),
    path('subscriptions/purchase/', UserSubscriptionViewSet.as_view({'post': 'purchase'})),
]