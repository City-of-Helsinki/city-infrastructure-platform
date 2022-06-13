from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
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
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new FurnitureSignpost Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all FurnitureSignpost Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single FurnitureSignpost Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single FurnitureSignpost Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single FurnitureSignpost Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single FurnitureSignpost Plan"),
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
        methods="post",
        description="Add one or more files to Furniture Signpost Plan",
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
        methods="delete",
        description="Delete single file from Furniture Signpost Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Furniture Signpost Plan",
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new FurnitureSignpost Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all FurnitureSignpost Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single FurnitureSignpost Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single FurnitureSignpost Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single FurnitureSignpost Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single FurnitureSignpost Real"),
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
        methods="post",
        description="Add one or more files to Furniture Signpost Real",
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
        methods="delete",
        description="Delete single file from Furniture Signpost Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Furniture Signpost Real",
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
