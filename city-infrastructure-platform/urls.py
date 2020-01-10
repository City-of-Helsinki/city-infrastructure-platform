from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

import traffic_control.views

router = routers.DefaultRouter()
router.register(
    "traffic-sign-plans", traffic_control.views.TrafficSignPlanViewSet,
)
router.register(
    "traffic-sign-reals", traffic_control.views.TrafficSignRealViewSet,
)

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("api/", include((router.urls, "api"), namespace="api")),
)

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)
