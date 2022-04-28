from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
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
    decorator=swagger_auto_schema(operation_description="Create new FurnitureSignpost Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all FurnitureSignpost Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single FurnitureSignpost Plan"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single FurnitureSignpost Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single FurnitureSignpost Plan"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Soft-delete single FurnitureSignpost Plan"),
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

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Furniture Signpost Plan",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Furniture Signpost Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Furniture Signpost Plan",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
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
    decorator=swagger_auto_schema(operation_description="Create new FurnitureSignpost Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all FurnitureSignpost Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single FurnitureSignpost Real"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single FurnitureSignpost Real"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(operation_description="Partially update single FurnitureSignpost Real"),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Soft-delete single FurnitureSignpost Real"),
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

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Furniture Signpost Real",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Furniture Signpost Real",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Furniture Signpost Real",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
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
