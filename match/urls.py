from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InteractionsViewSet, MatchActionViewSet, NearbyUsersView
# 
router = DefaultRouter()
router.register(r'matches', MatchActionViewSet, basename='match')
# router.register(r'visits', VisitViewSet, basename='visit')
router.register(r'interactions', InteractionsViewSet, basename='interactions')

urlpatterns = [
    path('', include(router.urls)),
    path('user-map/', NearbyUsersView.as_view(), name='user-map'),
]