from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from traffic_control.filters import (
    TrafficLightPlanFilterSet,
    TrafficLightRealFilterSet,
    TrafficLightRealOperationFilterSet,
)
from traffic_control.models import (
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
    TrafficLightRealOperation,
)
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
from traffic_control.serializers.traffic_light import (
    TrafficLightPlanFileSerializer,
    TrafficLightPlanGeoJSONSerializer,
    TrafficLightPlanSerializer,
    TrafficLightRealFileSerializer,
    TrafficLightRealGeoJSONSerializer,
    TrafficLightRealOperationSerializer,
    TrafficLightRealSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("TrafficLightPlanViewSet", "TrafficLightRealViewSet")


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new TrafficLight Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all TrafficLight Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single TrafficLight Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single TrafficLight Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single TrafficLight Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single TrafficLight Plan"),
)
class TrafficLightPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightPlanSerializer,
        "geojson": TrafficLightPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficLightPlan.objects.active()
    filterset_class = TrafficLightPlanFilterSet
    file_queryset = TrafficLightPlanFile.objects.all()
    file_serializer = TrafficLightPlanFileSerializer
    file_relation = "traffic_light_plan"

    @extend_schema(
        methods="post",
        description="Add one or more files to TrafficLight Plan",
        request=MultiFileUploadSchema,
        responses={200: TrafficLightPlanFileSerializer(many=True)},
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
        description="Delete single file from TrafficLight Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from TrafficLight Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: TrafficLightPlanFileSerializer},
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
    decorator=extend_schema(description="Create new TrafficLight Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all TrafficLight Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single TrafficLight Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single TrafficLight Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single TrafficLight Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single TrafficLight Real"),
)
class TrafficLightRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficLightReal.objects.active()
    filterset_class = TrafficLightRealFilterSet
    file_queryset = TrafficLightRealFile.objects.all()
    file_serializer = TrafficLightRealFileSerializer
    file_relation = "traffic_light_real"

    @extend_schema(
        methods="post",
        description="Add one or more files to TrafficLight Real",
        request=MultiFileUploadSchema,
        responses={200: TrafficLightRealFileSerializer(many=True)},
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
        description="Delete single file from TrafficLight Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from TrafficLight Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: TrafficLightRealFileSerializer},
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


class TrafficLightRealOperationViewSet(OperationViewSet):
    serializer_class = TrafficLightRealOperationSerializer
    queryset = TrafficLightRealOperation.objects.all()
    filterset_class = TrafficLightRealOperationFilterSet
