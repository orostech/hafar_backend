from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminUserViewSet, ConfigurationViewSet

router = DefaultRouter()
router.register(r'config', ConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]


admin_users_patterns = [
    path('users/', AdminUserViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('admin/users/<uuid:pk>/', AdminUserViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('admin/users/<uuid:pk>/reset-password/', AdminUserViewSet.as_view({'post': 'reset_password'})),
]
