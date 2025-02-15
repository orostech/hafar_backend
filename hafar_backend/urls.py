from django.contrib import admin
from django.urls import include, path
from rest_framework import views, response
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

from wallet.webhooks import flutterwave_webhook
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
]

apipatterns = [
    path('', include(v1patterns)),
]


urlpatterns = [
    # YOUR PATTERNS
    path("", APIRootView.as_view(), name='api-root'),
    path('', include(v1patterns)),
    path('v1/', include(apipatterns)),
    path('webhooks/flutterwave/', flutterwave_webhook, name='flutterwave-webhook'),
    path('test/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('admin/', admin.site.urls),
    ]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)