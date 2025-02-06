from django.contrib import admin
from django.urls import include, path
from rest_framework import views, response

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
    path("", APIRootView.as_view(), name='api-root'),
    path('admin/', admin.site.urls),
    path('', include(apipatterns)),
]
