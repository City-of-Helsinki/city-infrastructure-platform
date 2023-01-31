from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from traffic_control.filters import SignpostPlanFilterSet, SignpostRealFilterSet, SignpostRealOperationFilterSet
from traffic_control.models import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile, SignpostRealOperation
from traffic_control.schema import (
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.signpost import (
    SignpostPlanFileSerializer,
    SignpostPlanGeoJSONSerializer,
    SignpostPlanSerializer,
    SignpostRealFileSerializer,
    SignpostRealGeoJSONSerializer,
    SignpostRealOperationSerializer,
    SignpostRealSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("SignpostPlanViewSet", "SignpostRealViewSet")


@extend_schema_view(
    create=extend_schema(summary="Create new Signpost Plan"),
    list=extend_schema(summary="Retrieve all Signpost Plans"),
    retrieve=extend_schema(summary="Retrieve single Signpost Plan", parameters=[location_search_parameter]),
    update=extend_schema(summary="Update single Signpost Plan"),
    partial_update=extend_schema(summary="Partially update single Signpost Plan"),
    destroy=extend_schema(summary="Soft-delete single Signpost Plan"),
)
class SignpostPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": SignpostPlanSerializer,
        "geojson": SignpostPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = SignpostPlan.objects.active()
    filterset_class = SignpostPlanFilterSet
    file_queryset = SignpostPlanFile.objects.all()
    file_serializer = SignpostPlanFileSerializer
    file_relation = "signpost_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Signpost Plan",
        request=MultiFileUploadSchema,
        responses={200: SignpostPlanFileSerializer(many=True)},
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
        summary="Delete single file from Signpost Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Signpost Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: SignpostPlanFileSerializer},
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
    create=extend_schema(summary="Create new Signpost Real"),
    list=extend_schema(summary="Retrieve all Signpost Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Signpost Real"),
    update=extend_schema(summary="Update single Signpost Real"),
    partial_update=extend_schema(summary="Partially update single Signpost Real"),
    destroy=extend_schema(summary="Soft-delete single Signpost Real"),
)
class SignpostRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": SignpostRealSerializer,
        "geojson": SignpostRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = SignpostReal.objects.active()
    filterset_class = SignpostRealFilterSet
    file_queryset = SignpostRealFile.objects.all()
    file_serializer = SignpostRealFileSerializer
    file_relation = "signpost_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Signpost Real",
        request=MultiFileUploadSchema,
        responses={200: SignpostRealFileSerializer(many=True)},
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
        summary="Delete single file from Signpost Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Signpost Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: SignpostRealFileSerializer},
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
    create=extend_schema(summary="Add a new operation to a signpost real"),
    list=extend_schema(summary="Retrieve all operations of a signpost real"),
    retrieve=extend_schema(summary="Retrieve an operation of a signpost real"),
    update=extend_schema(summary="Update an operation of a signpost real"),
    partial_update=extend_schema(summary="Partially update an operation of a signpost real"),
    destroy=extend_schema(summary="Delete an operation of a signpost real"),
)
class SignpostRealOperationViewSet(OperationViewSet):
    serializer_class = SignpostRealOperationSerializer
    queryset = SignpostRealOperation.objects.all()
    filterset_class = SignpostRealOperationFilterSet
