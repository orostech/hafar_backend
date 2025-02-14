from django.contrib import admin
from django.urls import include, path
from rest_framework import views, response
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
class APIRootView(views.APIView):
    """
    A simple view to respond to GET requests to the root of the API.
    """
    def get(self, request):
        return views.Response({"message": "Welcome to the API. Use ____ for API access."})

v1patterns = [
     path("", include("config.urls")),
     path("", include("users.urls")),
     path("", include("match.urls")),
     path("", include("chat.urls")),
]

apipatterns = [
    path('v1/', include(v1patterns)),
]


urlpatterns = [
    # path("", APIRootView.as_view(), name='api-root'),
  
    # path('', include(apipatterns)),
]

urlpatterns = [
    # YOUR PATTERNS
    path("", APIRootView.as_view(), name='api-root'),
    path('', include(apipatterns)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('admin/', admin.site.urls),
    path('test/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)