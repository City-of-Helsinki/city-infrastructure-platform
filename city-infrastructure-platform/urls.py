from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers
from rest_framework_nested.routers import NestedSimpleRouter

from city_furniture.views import (
    city_furniture_color as city_furniture_color_views,
    city_furniture_device_type as city_furniture_device_type_views,
    city_furniture_target as city_furniture_target_views,
    furniture_signpost as furniture_signpost_views,
    responsible_entity as responsible_entity_views,
)
from map import views as map_views
from traffic_control.views import (
    additional_sign as additional_sign_views,
    barrier as barrier_views,
    mount as mount_views,
    operation_type as operation_type_views,
    operational_area as operational_area_views,
    owner as owner_views,
    plan as plan_views,
    road_marking as road_marking_views,
    signpost as signpost_views,
    traffic_light as traffic_light_views,
    traffic_sign as traffic_sign_views,
)
from traffic_control.views.wfs.views import CityInfrastructureWFSView

router = routers.DefaultRouter()
router.register("barrier-plans", barrier_views.BarrierPlanViewSet)
router.register("barrier-reals", barrier_views.BarrierRealViewSet)
router.register("traffic-light-plans", traffic_light_views.TrafficLightPlanViewSet)
router.register("traffic-light-reals", traffic_light_views.TrafficLightRealViewSet)
router.register("traffic-sign-plans", traffic_sign_views.TrafficSignPlanViewSet)
router.register("traffic-sign-reals", traffic_sign_views.TrafficSignRealViewSet)
router.register("additional-sign-plans", additional_sign_views.AdditionalSignPlanViewSet)
router.register("additional-sign-reals", additional_sign_views.AdditionalSignRealViewSet)
router.register("additional-sign-content-plans", additional_sign_views.AdditionalSignContentPlanViewSet)
router.register("additional-sign-content-reals", additional_sign_views.AdditionalSignContentRealViewSet)
router.register("mount-plans", mount_views.MountPlanViewSet)
router.register("mount-reals", mount_views.MountRealViewSet)
router.register("signpost-plans", signpost_views.SignpostPlanViewSet)
router.register("signpost-reals", signpost_views.SignpostRealViewSet)
router.register("road-marking-plans", road_marking_views.RoadMarkingPlanViewSet)
router.register("road-marking-reals", road_marking_views.RoadMarkingRealViewSet)
router.register("traffic-control-device-types", traffic_sign_views.TrafficControlDeviceTypeViewSet)
router.register("plans", plan_views.PlanViewSet)
router.register("portal-types", mount_views.PortalTypeViewSet)
router.register("mount-types", mount_views.MountTypeViewSet)
router.register("operational-areas", operational_area_views.OperationalAreaViewSet)
router.register("operation-types", operation_type_views.OperationTypeViewSet)
router.register("owners", owner_views.OwnerViewSet)

router.register("furniture-signpost-plans", furniture_signpost_views.FurnitureSignpostPlanViewSet)
router.register("furniture-signpost-reals", furniture_signpost_views.FurnitureSignpostRealViewSet)
router.register("city-furniture-device-types", city_furniture_device_type_views.CityFurnitureDeviceTypeViewSet)
router.register("city-furniture-targets", city_furniture_target_views.CityFurnitureTargetViewSet)
router.register("city-furniture-colors", city_furniture_color_views.CityFurnitureColorViewSet)
router.register("responsible-entity", responsible_entity_views.ResponsibleEntityViewSet)

# Nested routes for operations
# e.g. /barrier-reals/{id}/operations
barrier_operations_router = NestedSimpleRouter(router, "barrier-reals", lookup="barrier_real")
barrier_operations_router.register(
    "operations", barrier_views.BarrierRealOperationViewSet, basename="barrier-real-operations"
)

traffic_light_operations_router = NestedSimpleRouter(router, "traffic-light-reals", lookup="traffic_light_real")
traffic_light_operations_router.register(
    "operations", traffic_light_views.TrafficLightRealOperationViewSet, basename="traffic-light-real-operations"
)

traffic_sign_operations_router = NestedSimpleRouter(router, "traffic-sign-reals", lookup="traffic_sign_real")
traffic_sign_operations_router.register(
    "operations", traffic_sign_views.TrafficSignRealOperationViewSet, basename="traffic-sign-real-operations"
)

additional_sign_operations_router = NestedSimpleRouter(router, "additional-sign-reals", lookup="additional_sign_real")
additional_sign_operations_router.register(
    "operations", additional_sign_views.AdditionalSignRealOperationViewSet, basename="additional-sign-real-operations"
)

mount_operations_router = NestedSimpleRouter(router, "mount-reals", lookup="mount_real")
mount_operations_router.register("operations", mount_views.MountRealOperationViewSet, basename="mount-real-operations")

signpost_operations_router = NestedSimpleRouter(router, "signpost-reals", lookup="signpost_real")
signpost_operations_router.register(
    "operations", signpost_views.SignpostRealOperationViewSet, basename="signpost-real-operations"
)

road_marking_operations_router = NestedSimpleRouter(router, "road-marking-reals", lookup="road_marking_real")
road_marking_operations_router.register(
    "operations", road_marking_views.RoadMarkingRealOperationViewSet, basename="road-marking-real-operations"
)

furniture_signpost_operations_router = NestedSimpleRouter(
    router, "furniture-signpost-reals", lookup="furniture_signpost_real"
)
furniture_signpost_operations_router.register(
    "operations",
    furniture_signpost_views.FurnitureSignpostRealOperationViewSet,
    basename="furniture-signpost-real-operations",
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
    path("v1/", include((router.urls, "traffic_control"), namespace="v1")),
    path("v1/", include(barrier_operations_router.urls)),
    path("v1/", include(traffic_light_operations_router.urls)),
    path("v1/", include(traffic_sign_operations_router.urls)),
    path("v1/", include(additional_sign_operations_router.urls)),
    path("v1/", include(mount_operations_router.urls)),
    path("v1/", include(signpost_operations_router.urls)),
    path("v1/", include(road_marking_operations_router.urls)),
    path("v1/", include(furniture_signpost_operations_router.urls)),
    path("auth/", include("social_django.urls", namespace="social")),
    path("wfs/", CityInfrastructureWFSView.as_view(), name="wfs-city-infrastructure"),
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    re_path(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("sentry-debug/", lambda a: 1 / 0),
]

# Admin
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("map/", map_views.map_view, name="map-view"),
    path("map-config/", map_views.map_config, name="map-config"),
)

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
