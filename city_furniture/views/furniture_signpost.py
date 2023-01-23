from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from city_furniture.filters import (
    FurnitureSignpostPlanFilterSet,
    FurnitureSignpostRealFilterSet,
    FurnitureSignpostRealOperationFilterSet,
)
from city_furniture.models import (
    FurnitureSignpostPlan,
    FurnitureSignpostPlanFile,
    FurnitureSignpostReal,
    FurnitureSignpostRealFile,
    FurnitureSignpostRealOperation,
)
from city_furniture.serializers.furniture_signpost import (
    FurnitureSignpostPlanFileSerializer,
    FurnitureSignpostPlanGeoJSONSerializer,
    FurnitureSignpostPlanSerializer,
    FurnitureSignpostRealFileSerializer,
    FurnitureSignpostRealGeoJSONSerializer,
    FurnitureSignpostRealOperationSerializer,
    FurnitureSignpostRealSerializer,
)
from traffic_control.schema import (
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = (
    "FurnitureSignpostPlanViewSet",
    "FurnitureSignpostRealViewSet",
)


@extend_schema_view(
    create=extend_schema(summary="Create new FurnitureSignpost Plan"),
    list=extend_schema(summary="Retrieve all FurnitureSignpost Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single FurnitureSignpost Plan"),
    update=extend_schema(summary="Update single FurnitureSignpost Plan"),
    partial_update=extend_schema(summary="Partially update single FurnitureSignpost Plan"),
    destroy=extend_schema(summary="Soft-delete single FurnitureSignpost Plan"),
)
class FurnitureSignpostPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": FurnitureSignpostPlanSerializer,
        "geojson": FurnitureSignpostPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = FurnitureSignpostPlan.objects.active()
    filterset_class = FurnitureSignpostPlanFilterSet
    file_queryset = FurnitureSignpostPlanFile.objects.all()
    file_serializer = FurnitureSignpostPlanFileSerializer
    file_relation = "furniture_signpost_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Furniture Signpost Plan",
        request=MultiFileUploadSchema,
        responses={200: FurnitureSignpostPlanFileSerializer(many=True)},
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
        summary="Delete single file from Furniture Signpost Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Furniture Signpost Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: FurnitureSignpostPlanFileSerializer},
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
    create=extend_schema(summary="Create new FurnitureSignpost Real"),
    list=extend_schema(summary="Retrieve all FurnitureSignpost Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single FurnitureSignpost Real"),
    update=extend_schema(summary="Update single FurnitureSignpost Real"),
    partial_update=extend_schema(summary="Partially update single FurnitureSignpost Real"),
    destroy=extend_schema(summary="Soft-delete single FurnitureSignpost Real"),
)
class FurnitureSignpostRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": FurnitureSignpostRealSerializer,
        "geojson": FurnitureSignpostRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = FurnitureSignpostReal.objects.active()
    filterset_class = FurnitureSignpostRealFilterSet
    file_queryset = FurnitureSignpostRealFile.objects.all()
    file_serializer = FurnitureSignpostRealFileSerializer
    file_relation = "furniture_signpost_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Furniture Signpost Real",
        request=MultiFileUploadSchema,
        responses={200: FurnitureSignpostRealFileSerializer(many=True)},
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
        summary="Delete single file from Furniture Signpost Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Furniture Signpost Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: FurnitureSignpostRealFileSerializer},
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


class FurnitureSignpostRealOperationViewSet(OperationViewSet):
    serializer_class = FurnitureSignpostRealOperationSerializer
    queryset = FurnitureSignpostRealOperation.objects.all()
    filterset_class = FurnitureSignpostRealOperationFilterSet
