from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import (
    AdditionalSignContentPlanFilterSet,
    AdditionalSignContentRealFilterSet,
    AdditionalSignPlanFilterSet,
    AdditionalSignRealFilterSet,
)
from traffic_control.mixins import UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
)
from traffic_control.schema import location_parameter
from traffic_control.serializers import (
    AdditionalSignContentPlanSerializer,
    AdditionalSignContentRealSerializer,
    AdditionalSignPlanGeoJSONSerializer,
    AdditionalSignPlanSerializer,
    AdditionalSignRealGeoJSONSerializer,
    AdditionalSignRealSerializer,
)
from traffic_control.views._common import TrafficControlViewSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Create new AdditionalSign Plan"
    ),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all AdditionalSign Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single AdditionalSign Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single AdditionalSign Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single AdditionalSign Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single AdditionalSign Plan"
    ),
)
class AdditionalSignPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignPlanSerializer,
        "geojson": AdditionalSignPlanGeoJSONSerializer,
    }
    queryset = AdditionalSignPlan.objects.active()
    filterset_class = AdditionalSignPlanFilterSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Create new AdditionalSign Real"
    ),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all AdditionalSign Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single AdditionalSign Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single AdditionalSign Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single AdditionalSign Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single AdditionalSign Real"
    ),
)
class AdditionalSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignRealSerializer,
        "geojson": AdditionalSignRealGeoJSONSerializer,
    }
    queryset = AdditionalSignReal.objects.active()
    filterset_class = AdditionalSignRealFilterSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Create new AdditionalSignContent Plan"
    ),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all AdditionalSignContent Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single AdditionalSignContent Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single AdditionalSignContent Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single AdditionalSignContent Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single AdditionalSignContent Plan"
    ),
)
class AdditionalSignContentPlanViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["parent", "order"]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AdditionalSignContentPlanSerializer
    queryset = AdditionalSignContentPlan.objects.all()
    filterset_class = AdditionalSignContentPlanFilterSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(
        operation_description="Create new AdditionalSignContent Real"
    ),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all AdditionalSignContent Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single AdditionalSignContent Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single AdditionalSignContent Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single AdditionalSignContent Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single AdditionalSignContent Real"
    ),
)
class AdditionalSignContentRealViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["parent", "order"]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AdditionalSignContentRealSerializer
    queryset = AdditionalSignContentReal.objects.all()
    filterset_class = AdditionalSignContentRealFilterSet
