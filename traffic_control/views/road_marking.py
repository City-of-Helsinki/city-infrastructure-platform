from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from traffic_control.filters import (
    RoadMarkingPlanFilterSet,
    RoadMarkingRealFilterSet,
    RoadMarkingRealOperationFilterSet,
)
from traffic_control.mixins import ReplaceableModelMixin
from traffic_control.models import (
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
    RoadMarkingRealOperation,
)
from traffic_control.schema import (
    file_create_serializer,
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.road_marking import (
    RoadMarkingPlanFileSerializer,
    RoadMarkingPlanGeoJSONInputSerializer,
    RoadMarkingPlanGeoJSONOutputSerializer,
    RoadMarkingPlanInputSerializer,
    RoadMarkingPlanOutputSerializer,
    RoadMarkingRealFileSerializer,
    RoadMarkingRealGeoJSONSerializer,
    RoadMarkingRealOperationSerializer,
    RoadMarkingRealSerializer,
)
from traffic_control.services.road_marking import (
    road_marking_plan_get_active,
    road_marking_plan_soft_delete,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    prefetch_replacements,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("RoadMarkingPlanViewSet", "RoadMarkingRealViewSet")


@extend_schema_view(
    create=extend_schema(summary="Create new RoadMarking Plan"),
    list=extend_schema(summary="Retrieve all RoadMarking Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single RoadMarking Plan"),
    update=extend_schema(summary="Update single RoadMarking Plan"),
    partial_update=extend_schema(summary="Partially update single RoadMarking Plan"),
    destroy=extend_schema(summary="Soft-delete single RoadMarking Plan"),
)
class RoadMarkingPlanViewSet(TrafficControlViewSet, FileUploadViews, ReplaceableModelMixin):
    serializer_classes = {
        "default": RoadMarkingPlanOutputSerializer,
        "geojson": RoadMarkingPlanGeoJSONOutputSerializer,
        "input": RoadMarkingPlanInputSerializer,
        "input_geojson": RoadMarkingPlanGeoJSONInputSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = prefetch_replacements(road_marking_plan_get_active().prefetch_related("files"))

    filterset_class = RoadMarkingPlanFilterSet
    file_queryset = RoadMarkingPlanFile.objects.all()
    file_serializer = RoadMarkingPlanFileSerializer
    file_relation = "road_marking_plan"

    def get_list_queryset(self):
        return prefetch_replacements(road_marking_plan_get_active()).prefetch_related("files")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        road_marking_plan_soft_delete(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to RoadMarking Plan",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(RoadMarkingPlanFileSerializer)},
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
        summary="Delete single file from RoadMarking Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from RoadMarking Plan",
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


@extend_schema_view(
    create=extend_schema(summary="Create new RoadMarking Real"),
    list=extend_schema(summary="Retrieve all RoadMarking Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single RoadMarking Real"),
    update=extend_schema(summary="Update single RoadMarking Real"),
    partial_update=extend_schema(summary="Partially update single RoadMarking Real"),
    destroy=extend_schema(summary="Soft-delete single RoadMarking Real"),
)
class RoadMarkingRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = (
        RoadMarkingReal.objects.active()
        .prefetch_related("files")
        .prefetch_related("operations")
        .prefetch_related("operations__operation_type")
        .select_related("road_marking_plan__plan")
    )
    filterset_class = RoadMarkingRealFilterSet
    file_queryset = RoadMarkingRealFile.objects.all()
    file_serializer = RoadMarkingRealFileSerializer
    file_relation = "road_marking_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to RoadMarking Real",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(RoadMarkingRealFileSerializer)},
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
        summary="Delete single file from RoadMarking Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from RoadMarking Real",
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


@extend_schema_view(
    create=extend_schema(summary="Add a new operation to a road marking real"),
    list=extend_schema(summary="Retrieve all operations of a road marking real"),
    retrieve=extend_schema(summary="Retrieve an operation of a road marking real"),
    update=extend_schema(summary="Update an operation of a road marking real"),
    partial_update=extend_schema(summary="Partially update an operation of a road marking real"),
    destroy=extend_schema(summary="Delete an operation of a road marking real"),
)
class RoadMarkingRealOperationViewSet(OperationViewSet):
    serializer_class = RoadMarkingRealOperationSerializer
    queryset = RoadMarkingRealOperation.objects.all()
    filterset_class = RoadMarkingRealOperationFilterSet
