from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema

from traffic_control.filters import PlanFilterSet
from traffic_control.models import Plan
from traffic_control.schema import location_parameter
from traffic_control.serializers.plan import PlanGeoJSONSerializer, PlanSerializer
from traffic_control.views._common import TrafficControlViewSet


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(
        description="Partially update single Plan",
    ),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(
        description="Soft-delete single Plan",
    ),
)
class PlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": PlanSerializer,
        "geojson": PlanGeoJSONSerializer,
    }
    queryset = Plan.objects.active()
    filterset_class = PlanFilterSet
