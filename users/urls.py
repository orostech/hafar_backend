# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
# from 

router = DefaultRouter()
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'photos', views.UserPhotoViewSet, basename='photo')
router.register(r'videos', views.UserVideoViewSet, basename='video')
router.register(r'blocks', views.UserBlockViewSet, basename='block')
router.register(r'ratings', views.UserRatingViewSet, basename='rating')




urlpatterns = [
     path('', include(router.urls)),
       path('update-device-token/', views.update_device_token, name='register'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend-verification'),
        path('auth/password-reset/request/', views.PasswordResetRequestView.as_view()),
    path('auth/password-reset/verify/', views.PasswordResetVerifyView.as_view()),
    path('auth/password-reset/confirm/', views.PasswordResetConfirmView.as_view()),
        path("states/", views.StateListView.as_view(), name="state-list"),
    path("lgas/", views.LGAListView.as_view(), name="lga-list"),
]