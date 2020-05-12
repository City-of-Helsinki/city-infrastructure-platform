from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from traffic_control.views import (
    barrier as barrier_views,
    mount as mount_views,
    road_marking as road_marking_views,
    signpost as signpost_views,
    traffic_light as traffic_light_views,
    traffic_sign as traffic_sign_views,
)

router = routers.DefaultRouter()
router.register(
    "barrier-plans", barrier_views.BarrierPlanViewSet,
)
router.register(
    "barrier-reals", barrier_views.BarrierRealViewSet,
)
router.register(
    "traffic-light-plans", traffic_light_views.TrafficLightPlanViewSet,
)
router.register(
    "traffic-light-reals", traffic_light_views.TrafficLightRealViewSet,
)
router.register(
    "traffic-sign-plans", traffic_sign_views.TrafficSignPlanViewSet,
)
router.register(
    "traffic-sign-reals", traffic_sign_views.TrafficSignRealViewSet,
)
router.register(
    "mount-plans", mount_views.MountPlanViewSet,
)
router.register(
    "mount-reals", mount_views.MountRealViewSet,
)
router.register(
    "signpost-plans", signpost_views.SignpostPlanViewSet,
)
router.register(
    "signpost-reals", signpost_views.SignpostRealViewSet,
)
router.register(
    "road-marking-plans", road_marking_views.RoadMarkingPlanViewSet,
)
router.register(
    "road-marking-reals", road_marking_views.RoadMarkingRealViewSet,
)
router.register(
    "traffic-sign-codes", traffic_sign_views.TrafficSignCodeViewSet,
)
router.register(
    "portal-types", mount_views.PortalTypeViewSet,
)
schema_view = get_schema_view(
    openapi.Info(
        title="City Infrastructure Platform REST API",
        default_version="v1",
        description="""
            <b>Traffic Control devices</b>

            Provides REST API for Traffic Control devices, such as Traffic Signs, Traffic Lights, Barriers,
            SignPosts, Mounts and Road Markings.

            These devices have planned and realized entities in the platform and therefore also equivalent
            REST-endpoints.

            Entity location output format can be controlled via "geo_format" GET-parameter.
            Supported formats are ewkt and geojson. EWKT is the default format.
        """,
        terms_of_service="https://opensource.org/licenses/MIT",
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    validators=["ssv"],
)

urlpatterns = [
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
    path("sentry-debug/", lambda a: 1 / 0),
]

urlpatterns += i18n_patterns(path("admin/", admin.site.urls),)

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
