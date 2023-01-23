from drf_spectacular.utils import extend_schema, extend_schema_view

from traffic_control.filters import PlanFilterSet
from traffic_control.models import Plan
from traffic_control.schema import location_search_parameter
from traffic_control.serializers.plan import PlanGeoJSONSerializer, PlanSerializer
from traffic_control.views._common import TrafficControlViewSet


@extend_schema_view(
    create=extend_schema(summary="Create new Plan"),
    list=extend_schema(summary="Retrieve all Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Plan"),
    update=extend_schema(summary="Update single Plan"),
    partial_update=extend_schema(summary="Partially update single Plan"),
    destroy=extend_schema(summary="Soft-delete single Plan"),
)
class PlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": PlanSerializer,
        "geojson": PlanGeoJSONSerializer,
    }
    queryset = Plan.objects.active()
    filterset_class = PlanFilterSet
