from drf_spectacular.utils import extend_schema, extend_schema_view

from traffic_control.filters import (
    AdditionalSignPlanFilterSet,
    AdditionalSignRealFilterSet,
    AdditionalSignRealOperationFilterSet,
)
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, AdditionalSignRealOperation
from traffic_control.schema import location_search_parameter
from traffic_control.serializers.additional_sign import (
    AdditionalSignPlanGeoJSONSerializer,
    AdditionalSignPlanSerializer,
    AdditionalSignRealGeoJSONSerializer,
    AdditionalSignRealOperationSerializer,
    AdditionalSignRealSerializer,
)
from traffic_control.views._common import OperationViewSet, ResponsibleEntityPermission, TrafficControlViewSet


@extend_schema_view(
    create=extend_schema(summary="Create new AdditionalSign Plan"),
    list=extend_schema(summary="Retrieve all AdditionalSign Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single AdditionalSign Plan"),
    update=extend_schema(summary="Update single AdditionalSign Plan"),
    partial_update=extend_schema(summary="Partially update single AdditionalSign Plan"),
    destroy=extend_schema(summary="Soft-delete single AdditionalSign Plan"),
)
class AdditionalSignPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": AdditionalSignPlanSerializer,
        "geojson": AdditionalSignPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = AdditionalSignPlan.objects.active()
    filterset_class = AdditionalSignPlanFilterSet


@extend_schema_view(
    create=extend_schema(summary="Create new AdditionalSign Real"),
    list=extend_schema(summary="Retrieve all AdditionalSign Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single AdditionalSign Real"),
    update=extend_schema(summary="Update single AdditionalSign Real"),
    partial_update=extend_schema(summary="Partially update single AdditionalSign Real"),
    destroy=extend_schema(summary="Soft-delete single AdditionalSign Real"),
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


@extend_schema_view(
    create=extend_schema(summary="Add a new operation to an additional sign real"),
    list=extend_schema(summary="Retrieve all operations of an additional sign real"),
    retrieve=extend_schema(summary="Retrieve an operation of an additional sign real"),
    update=extend_schema(summary="Update an operation of an additional sign real"),
    partial_update=extend_schema(summary="Partially update an operation of an additional sign real"),
    destroy=extend_schema(summary="Delete an operation of an additional sign real"),
)
class AdditionalSignRealOperationViewSet(OperationViewSet):
    serializer_class = AdditionalSignRealOperationSerializer
    queryset = AdditionalSignRealOperation.objects.all()
    filterset_class = AdditionalSignRealOperationFilterSet
