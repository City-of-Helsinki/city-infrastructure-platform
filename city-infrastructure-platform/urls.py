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
    "barrier-plans", traffic_control.views.BarrierPlanViewSet,
)
router.register(
    "barrier-reals", traffic_control.views.BarrierRealViewSet,
)
router.register(
    "traffic-light-plans", traffic_control.views.TrafficLightPlanViewSet,
)
router.register(
    "traffic-light-reals", traffic_control.views.TrafficLightRealViewSet,
)
router.register(
    "traffic-sign-plans", traffic_control.views.TrafficSignPlanViewSet,
)
router.register(
    "traffic-sign-reals", traffic_control.views.TrafficSignRealViewSet,
)
router.register(
    "mount-plans", traffic_control.views.MountPlanViewSet,
)
router.register(
    "mount-reals", traffic_control.views.MountRealViewSet,
)
router.register(
    "signpost-plans", traffic_control.views.SignpostPlanViewSet,
)
router.register(
    "signpost-reals", traffic_control.views.SignpostRealViewSet,
)
router.register(
    "road-marking-plans", traffic_control.views.RoadMarkingPlanViewSet,
)
router.register(
    "road-marking-reals", traffic_control.views.RoadMarkingRealViewSet,
)
router.register(
    "traffic-sign-codes", traffic_control.views.TrafficSignCodeViewSet,
)
router.register(
    "portal-types", traffic_control.views.PortalTypeViewSet,
)
schema_view = get_schema_view(
    openapi.Info(
        title="City Infrastructure Platform API",
        default_version="v1",
        description="REST API for City Infrastructure Platform",
        terms_of_service="https://opensource.org/licenses/MIT",
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    validators=["ssv"],
)

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("ha/", include("helusers.urls", namespace="helusers")),
    path("api/", include((router.urls, "api"), namespace="api")),
    path("auth/", include("social_django.urls", namespace="social")),
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

urlpatterns.append(path("sentry-debug/", lambda a: 1 / 0))

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
