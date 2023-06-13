from drf_spectacular.utils import extend_schema, extend_schema_view
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
from traffic_control.schema import (
    file_create_serializer,
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
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


@extend_schema_view(
    create=extend_schema(summary="Create new TrafficLight Plan"),
    list=extend_schema(summary="Retrieve all TrafficLight Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single TrafficLight Plan"),
    update=extend_schema(summary="Update single TrafficLight Plan"),
    partial_update=extend_schema(summary="Partially update single TrafficLight Plan"),
    destroy=extend_schema(summary="Soft-delete single TrafficLight Plan"),
)
class TrafficLightPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightPlanSerializer,
        "geojson": TrafficLightPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficLightPlan.objects.active().prefetch_related("files")
    filterset_class = TrafficLightPlanFilterSet
    file_queryset = TrafficLightPlanFile.objects.all()
    file_serializer = TrafficLightPlanFileSerializer
    file_relation = "traffic_light_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to TrafficLight Plan",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(TrafficLightPlanFileSerializer)},
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
        methods=("delete",),
        summary="Delete single file from TrafficLight Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from TrafficLight Plan",
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


@extend_schema_view(
    create=extend_schema(summary="Create new TrafficLight Real"),
    list=extend_schema(summary="Retrieve all TrafficLight Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single TrafficLight Real"),
    update=extend_schema(summary="Update single TrafficLight Real"),
    partial_update=extend_schema(summary="Partially update single TrafficLight Real"),
    destroy=extend_schema(summary="Soft-delete single TrafficLight Real"),
)
class TrafficLightRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = (
        TrafficLightReal.objects.active()
        .prefetch_related("files")
        .prefetch_related("operations")
        .prefetch_related("operations__operation_type")
    )
    filterset_class = TrafficLightRealFilterSet
    file_queryset = TrafficLightRealFile.objects.all()
    file_serializer = TrafficLightRealFileSerializer
    file_relation = "traffic_light_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to TrafficLight Real",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(TrafficLightRealFileSerializer)},
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
        methods=("delete",),
        summary="Delete single file from TrafficLight Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from TrafficLight Real",
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


@extend_schema_view(
    create=extend_schema(summary="Add a new operation to a traffic light real"),
    list=extend_schema(summary="Retrieve all operations of a traffic light real"),
    retrieve=extend_schema(summary="Retrieve an operation of a traffic light real"),
    update=extend_schema(summary="Update an operation of a traffic light real"),
    partial_update=extend_schema(summary="Partially update an operation of a traffic light real"),
    destroy=extend_schema(summary="Delete an operation of a traffic light real"),
)
class TrafficLightRealOperationViewSet(OperationViewSet):
    serializer_class = TrafficLightRealOperationSerializer
    queryset = TrafficLightRealOperation.objects.all()
    filterset_class = TrafficLightRealOperationFilterSet
