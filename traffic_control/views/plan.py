from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from traffic_control.filters import PlanFilterSet
from traffic_control.models import Plan
from traffic_control.schema import location_search_parameter
from traffic_control.serializers.plan import PlanGeoJSONSerializer, PlanSerializer
from traffic_control.views._common import TrafficControlViewSet
from traffic_control.views.bulk_plan_insert import (
    BULK_PLAN_INSERT_MOCK_BATCH_PAYLOAD,
    BulkPlanInputResponseSerializer,
    BulkPlanInputSerializer,
)


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
    queryset = (
        Plan.objects.active()
        .prefetch_related("additional_sign_plans")
        .prefetch_related("barrier_plans")
        .prefetch_related("mount_plans")
        .prefetch_related("road_marking_plans")
        .prefetch_related("signpost_plans")
        .prefetch_related("traffic_light_plans")
        .prefetch_related("traffic_sign_plans")
        .prefetch_related("furniture_signpost_plans")
    )
    filterset_class = PlanFilterSet

    @extend_schema(
        summary="Bulk create plans and their dependent objects in one atomic transaction",
        description=(
            "The endpoint expects the client itself to provide UUIDs to the new objects. In additional to basic field "
            "validation, the endpoint also checks for the presence of dependency cycles in the input data."
        ),
        examples=[
            OpenApiExample(
                name="Complete Interdependent Pipeline Example",
                description=(
                    "A complex operation passing a Plan, a derived MountPlan, and connected Traffic Signs using "
                    "cross-referencing string IDs."
                ),
                value=BULK_PLAN_INSERT_MOCK_BATCH_PAYLOAD,
                request_only=True,
            )
        ],
        request=BulkPlanInputSerializer,
        responses={201: BulkPlanInputResponseSerializer, 400: dict},
        methods=("POST",),
    )
    @action(
        detail=False,
        methods=["POST"],
        url_path="bulk-insert",
    )
    def bulk_insert(self, request, *args, **kwargs):
        input_serializer = BulkPlanInputSerializer(data=request.data, context={"request": request})
        input_serializer.is_valid(raise_exception=True)
        created_instances = input_serializer.save()
        response_serializer = BulkPlanInputResponseSerializer(created_instances, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
