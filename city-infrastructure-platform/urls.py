from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

import traffic_control.views

router = routers.DefaultRouter()
router.register(
    "traffic-sign-plans", traffic_control.views.TrafficSignPlanViewSet,
)
router.register(
    "traffic-sign-reals", traffic_control.views.TrafficSignRealViewSet,
)
router.register(
    "mount-plans", traffic_control.views.MountPlanViewSet,
)

schema_view = get_schema_view(
    openapi.Info(
        title="City Infrastructure Platform API",
        default_version="0.0.1",
        description="REST API for City Infrastructure Platform",
        terms_of_service="https://opensource.org/licenses/MIT",
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("api/", include((router.urls, "api"), namespace="api")),
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    url(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    url(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
)

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)
