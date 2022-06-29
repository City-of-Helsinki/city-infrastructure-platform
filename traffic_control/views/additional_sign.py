from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import (
    AdditionalSignContentPlanFilterSet,
    AdditionalSignContentRealFilterSet,
    AdditionalSignPlanFilterSet,
    AdditionalSignRealFilterSet,
    AdditionalSignRealOperationFilterSet,
)
from traffic_control.mixins import UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
    AdditionalSignRealOperation,
)
from traffic_control.schema import location_parameter
from traffic_control.serializers.additional_sign import (
    AdditionalSignContentPlanSerializer,
    AdditionalSignContentRealSerializer,
    AdditionalSignPlanGeoJSONSerializer,
    AdditionalSignPlanSerializer,
    AdditionalSignRealGeoJSONSerializer,
    AdditionalSignRealOperationSerializer,
    AdditionalSignRealSerializer,
)
from traffic_control.views._common import OperationViewSet, ResponsibleEntityPermission, TrafficControlViewSet


@method_decorator(
    name="create",
    decorator=extend_schema(description=("Create new AdditionalSign Plan and AdditionalSignContent Plans")),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all AdditionalSign Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single AdditionalSign Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description=("Update single AdditionalSign Plan and AdditionalSignContent Plans")),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(
        description=("Partially update single AdditionalSign Plan and " "AdditionalSignContent Plans")
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single AdditionalSign Plan"),
)
class AdditionalSignPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignPlanSerializer,
        "geojson": AdditionalSignPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = AdditionalSignPlan.objects.active()
    filterset_class = AdditionalSignPlanFilterSet


@method_decorator(
    name="create",
    decorator=extend_schema(
        description=("Create new AdditionalSign Real and AdditionalSignContent Reals"),
    ),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all AdditionalSign Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single AdditionalSign Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description=("Update single AdditionalSign Real and AdditionalSignContent Reals")),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(
        description=("Partially update single AdditionalSign Real and " "AdditionalSignContent Reals")
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single AdditionalSign Real"),
)
class AdditionalSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignRealSerializer,
        "geojson": AdditionalSignRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = AdditionalSignReal.objects.none()
    filterset_class = AdditionalSignRealFilterSet

    def get_queryset(self):
        queryset = AdditionalSignReal.objects.active()
        return queryset.prefetch_related(
            "content",
            "content__device_type",
            "content__created_by",
            "content__updated_by",
        )

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


@method_decorator(
    name="create",
    decorator=extend_schema(description=("Create new AdditionalSignContent Plan and AdditionalSignContent Plans")),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all AdditionalSignContent Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single AdditionalSignContent Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single AdditionalSignContent Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single AdditionalSignContent Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single AdditionalSignContent Plan"),
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
    decorator=extend_schema(description="Create new AdditionalSignContent Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all AdditionalSignContent Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single AdditionalSignContent Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single AdditionalSignContent Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single AdditionalSignContent Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single AdditionalSignContent Real"),
)
class AdditionalSignContentRealViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["parent", "order"]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AdditionalSignContentRealSerializer
    queryset = AdditionalSignContentReal.objects.all()
    filterset_class = AdditionalSignContentRealFilterSet


class AdditionalSignRealOperationViewSet(OperationViewSet):
    serializer_class = AdditionalSignRealOperationSerializer
    queryset = AdditionalSignRealOperation.objects.all()
    filterset_class = AdditionalSignRealOperationFilterSet
