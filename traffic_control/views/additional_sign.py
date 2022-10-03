from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema

from traffic_control.filters import (
    AdditionalSignPlanFilterSet,
    AdditionalSignRealFilterSet,
    AdditionalSignRealOperationFilterSet,
)
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, AdditionalSignRealOperation
from traffic_control.schema import location_parameter
from traffic_control.serializers.additional_sign import (
    AdditionalSignPlanGeoJSONSerializer,
    AdditionalSignPlanSerializer,
    AdditionalSignRealGeoJSONSerializer,
    AdditionalSignRealOperationSerializer,
    AdditionalSignRealSerializer,
)
from traffic_control.views._common import OperationViewSet, ResponsibleEntityPermission, TrafficControlViewSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description=("Create new AdditionalSign Plan")),
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
    decorator=swagger_auto_schema(operation_description="Retrieve single AdditionalSign Plan"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description=("Update single AdditionalSign Plan")),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description=("Partially update single AdditionalSign Plan")),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Soft-delete single AdditionalSign Plan"),
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
    decorator=swagger_auto_schema(
        operation_description=("Create new AdditionalSign Real"),
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
    decorator=swagger_auto_schema(operation_description="Retrieve single AdditionalSign Real"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description=("Update single AdditionalSign Real")),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description=("Partially update single AdditionalSign Real")),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Soft-delete single AdditionalSign Real"),
)
class AdditionalSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignRealSerializer,
        "geojson": AdditionalSignRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = AdditionalSignReal.objects.active()
    filterset_class = AdditionalSignRealFilterSet

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class AdditionalSignRealOperationViewSet(OperationViewSet):
    serializer_class = AdditionalSignRealOperationSerializer
    queryset = AdditionalSignRealOperation.objects.all()
    filterset_class = AdditionalSignRealOperationFilterSet
