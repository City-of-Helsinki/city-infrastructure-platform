from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from ..filters import RoadMarkingPlanFilterSet, RoadMarkingRealFilterSet
from ..models import RoadMarkingPlan, RoadMarkingPlanFile, RoadMarkingReal
from ..serializers import (
    RoadMarkingPlanFileSerializer,
    RoadMarkingPlanGeoJSONSerializer,
    RoadMarkingPlanPostFileSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingRealGeoJSONSerializer,
    RoadMarkingRealSerializer,
)
from ._common import FileUploadViews, location_parameter, TrafficControlViewSet

__all__ = ("RoadMarkingPlanViewSet", "RoadMarkingRealViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new RoadMarking Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all RoadMarking Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single RoadMarking Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single RoadMarking Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single RoadMarking Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single RoadMarking Plan"
    ),
)
class RoadMarkingPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": RoadMarkingPlanSerializer,
        "geojson": RoadMarkingPlanGeoJSONSerializer,
    }
    queryset = RoadMarkingPlan.objects.active()
    filterset_class = RoadMarkingPlanFilterSet
    file_queryset = RoadMarkingPlanFile.objects.all()
    file_serializer = RoadMarkingPlanFileSerializer
    file_relation = "road_marking_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add single file to RoadMarking Plan",
        request_body=RoadMarkingPlanPostFileSerializer,
        responses={200: RoadMarkingPlanFileSerializer},
    )
    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_file(self, request, *args, **kwargs):
        return super().post_file(request, *args, **kwargs)

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from RoadMarking Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from RoadMarking Plan",
        request_body=RoadMarkingPlanPostFileSerializer,
        responses={200: RoadMarkingPlanFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new RoadMarking Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all RoadMarking Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single RoadMarking Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single RoadMarking Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single RoadMarking Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single RoadMarking Real"
    ),
)
class RoadMarkingRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    queryset = RoadMarkingReal.objects.active()
    filterset_class = RoadMarkingRealFilterSet
