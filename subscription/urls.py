from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPaymentView, SubscriptionPlanViewSet, SubscriptionVerifyPaymentView, UserSubscriptionViewSet

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscription-plans')
router.register(r'subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')



urlpatterns = [
    path('', include(router.urls)),
    path('subscriptions/purchase/', UserSubscriptionViewSet.as_view({'post': 'purchase'})),
    path('subscription-payment/', SubscriptionPaymentView.as_view(), name='subscription-payment'),
    path('subscription-payment/verify/', SubscriptionVerifyPaymentView.as_view(), name='verify-subscription-payment'),

#    path('subscription-payment/verify/', SubscriptionPaymentView.as_view(), name='verify-subscription-payment'),

]