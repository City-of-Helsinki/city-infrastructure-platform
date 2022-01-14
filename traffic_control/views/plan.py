from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema

from traffic_control.filters import PlanFilterSet
from traffic_control.models import Plan
from traffic_control.schema import location_parameter
from traffic_control.serializers.plan import PlanGeoJSONSerializer, PlanSerializer
from traffic_control.views._common import TrafficControlViewSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Plan"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Plan",
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Plan",
    ),
)
class PlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": PlanSerializer,
        "geojson": PlanGeoJSONSerializer,
    }
    queryset = Plan.objects.active()
    filterset_class = PlanFilterSet
