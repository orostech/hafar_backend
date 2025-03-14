from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminUserViewSet, ConfigurationViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'config', ConfigurationViewSet)

admin_router = DefaultRouter()
admin_router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]


admin_users_patterns = [
      path('', include(admin_router.urls)),
    path('users/', AdminUserViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('admin/users/<uuid:pk>/', AdminUserViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('admin/users/<uuid:pk>/reset-password/', AdminUserViewSet.as_view({'post': 'reset_password'})),
]
