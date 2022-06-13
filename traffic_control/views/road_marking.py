from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from traffic_control.filters import (
    RoadMarkingPlanFilterSet,
    RoadMarkingRealFilterSet,
    RoadMarkingRealOperationFilterSet,
)
from traffic_control.models import (
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
    RoadMarkingRealOperation,
)
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
from traffic_control.serializers.road_marking import (
    RoadMarkingPlanFileSerializer,
    RoadMarkingPlanGeoJSONSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingRealFileSerializer,
    RoadMarkingRealGeoJSONSerializer,
    RoadMarkingRealOperationSerializer,
    RoadMarkingRealSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("RoadMarkingPlanViewSet", "RoadMarkingRealViewSet")


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new RoadMarking Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all RoadMarking Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single RoadMarking Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single RoadMarking Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single RoadMarking Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single RoadMarking Plan"),
)
class RoadMarkingPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": RoadMarkingPlanSerializer,
        "geojson": RoadMarkingPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = RoadMarkingPlan.objects.active()
    filterset_class = RoadMarkingPlanFilterSet
    file_queryset = RoadMarkingPlanFile.objects.all()
    file_serializer = RoadMarkingPlanFileSerializer
    file_relation = "road_marking_plan"

    @extend_schema(
        methods="post",
        description="Add one or more files to RoadMarking Plan",
        request=MultiFileUploadSchema,
        responses={200: RoadMarkingPlanFileSerializer(many=True)},
    )
    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_files(self, request, *args, **kwargs):
        return super().post_files(request, *args, **kwargs)

    @extend_schema(
        methods="delete",
        description="Delete single file from RoadMarking Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from RoadMarking Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: RoadMarkingPlanFileSerializer},
    )
    @action(
        methods=(
            "PATCH",
            "DELETE",
        ),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new RoadMarking Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all RoadMarking Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single RoadMarking Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single RoadMarking Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single RoadMarking Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single RoadMarking Real"),
)
class RoadMarkingRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = RoadMarkingReal.objects.active()
    filterset_class = RoadMarkingRealFilterSet
    file_queryset = RoadMarkingRealFile.objects.all()
    file_serializer = RoadMarkingRealFileSerializer
    file_relation = "road_marking_real"

    @extend_schema(
        methods="post",
        description="Add one or more files to RoadMarking Real",
        request=MultiFileUploadSchema,
        responses={200: RoadMarkingRealFileSerializer(many=True)},
    )
    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_files(self, request, *args, **kwargs):
        return super().post_files(request, *args, **kwargs)

    @extend_schema(
        methods="delete",
        description="Delete single file from RoadMarking Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from RoadMarking Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: RoadMarkingRealFileSerializer},
    )
    @action(
        methods=(
            "PATCH",
            "DELETE",
        ),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)


class RoadMarkingRealOperationViewSet(OperationViewSet):
    serializer_class = RoadMarkingRealOperationSerializer
    queryset = RoadMarkingRealOperation.objects.all()
    filterset_class = RoadMarkingRealOperationFilterSet
