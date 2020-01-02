from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from traffic_control import api as traffic_control_api
from users import api as users_api

router = routers.DefaultRouter()
router.register("users", users_api.UserViewSet)
router.register("groups", users_api.GroupViewSet)
router.register(
    "trafficsignplans", traffic_control_api.TrafficSignPlanViewSet,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((router.urls, "api"), namespace="api")),
]

if settings.DEBUG:
    # Serve media from development server
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)
