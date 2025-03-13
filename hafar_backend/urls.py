from django.contrib import admin
from django.urls import include, path
from rest_framework import views, response
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from match.models import Match
from notification.email_service import EmailService
from notification.services import FirebaseNotificationService
from wallet.webhooks import flutterwave_webhook
from django.shortcuts import render
from config.urls import admin_users_patterns
class APIRootView(views.APIView):
    """
    A simple view to respond to GET requests to the root of the API.
    """
    def get(self, request):
        return views.Response({"message": "Welcome to the API. Use ____ for API access."})

v1patterns = [
     path("", include("config.urls")),
     path("gifts/", include('gift.urls')),
     path("", include("users.urls")),
     path("", include("match.urls")),
     path("", include("chat.urls")),
     path("", include("wallet.urls")),
     path("", include("subscription.urls")),
     path("", include("notification.urls")),
]

apipatterns = [
    path('', include(v1patterns)),
]
class APIIRootView(views.APIView):
    """
    A simple view to respond to GET requests to the root of the API.
    """
    def get(self, request):
        try:
            context = {
                'user': request.user,
                'matched_with': request.user,  # Replace with actual matched user
                'match_url': f"{settings.FRONTEND_URL}/matches/123",  # Replace with actual match ID
                'site_name': 'Hafar',
                'play_store_url':"https://play.google.com/store/apps/details?id=com.orostech.hafar"
            }
            try:
                EmailService().send_revival_announcement()
                # send_welcome_email(request.user)
                pass
            except Exception as e:
               print(f"email notification failed: {str(e)}")
            return render(request, 'emails/platform_back_announcement.html', context)
        except:
            return views.Response({"message": "failed."})


# ="https://https://hafar.sfo3.digitaloceanspaces.com/static/admin/css/nav_sidebar.css

        # FirebaseNotificationService.send_push_notification(
        #         recipient=request.user,
        #         title='title_template',
        #         body='body_template',
        #         data={
        #             # 'type': verb,
        #             # 'id': str(18392),
        #             # 'actor_id': str(actor.id)
        #         }
        #     )
        # return views.Response({"message": "access."})


urlpatterns = [
    # YOUR PATTERNS
    path("", APIRootView.as_view(), name='api-root'),
    path('', include(v1patterns)),
    path('v1/', include(apipatterns)),
    path('a1/', include(admin_users_patterns)),
    path('webhooks/flutterwave/', flutterwave_webhook, name='flutterwave-webhook'),
    path('test/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('admin/', admin.site.urls),

    #  path("mm/", APIIRootView.as_view(), name='apii-root'),

    ]

if settings.DEBUG:
    urlpatterns.append(path("mm/", APIIRootView.as_view(), name='apii-root'))



# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)