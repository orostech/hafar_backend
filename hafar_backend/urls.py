from django.contrib import admin
from django.urls import include, path

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
    path('admin/', admin.site.urls),
    path('', include(apipatterns)),
]
