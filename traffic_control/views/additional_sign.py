from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from traffic_control.filters import (
    AdditionalSignPlanFilterSet,
    AdditionalSignRealFilterSet,
    AdditionalSignRealOperationFilterSet,
)
from traffic_control.models import (
    AdditionalSignPlanFile,
    AdditionalSignReal,
    AdditionalSignRealFile,
    AdditionalSignRealOperation,
)
from traffic_control.schema import (
    file_create_serializer,
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.additional_sign import (
    AdditionalSignPlanFileSerializer,
    AdditionalSignPlanGeoJSONInputSerializer,
    AdditionalSignPlanGeoJSONOutputSerializer,
    AdditionalSignPlanInputSerializer,
    AdditionalSignPlanOutputSerializer,
    AdditionalSignRealFileSerializer,
    AdditionalSignRealGeoJSONSerializer,
    AdditionalSignRealOperationSerializer,
    AdditionalSignRealSerializer,
)
from traffic_control.services.additional_sign import (
    additional_sign_plan_get_active,
    additional_sign_plan_get_current,
    additional_sign_plan_soft_delete,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    prefetch_replacements,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)


@extend_schema_view(
    create=extend_schema(summary="Create new AdditionalSign Plan"),
    list=extend_schema(summary="Retrieve all AdditionalSign Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single AdditionalSign Plan"),
    update=extend_schema(summary="Update single AdditionalSign Plan"),
    partial_update=extend_schema(summary="Partially update single AdditionalSign Plan"),
    destroy=extend_schema(summary="Soft-delete single AdditionalSign Plan"),
)
class AdditionalSignPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": AdditionalSignPlanOutputSerializer,
        "geojson": AdditionalSignPlanGeoJSONOutputSerializer,
        "input": AdditionalSignPlanInputSerializer,
        "input_geojson": AdditionalSignPlanGeoJSONInputSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = prefetch_replacements(additional_sign_plan_get_active())
    filterset_class = AdditionalSignPlanFilterSet
    file_queryset = AdditionalSignPlanFile.objects.all()
    file_serializer = AdditionalSignPlanFileSerializer
    file_relation = "additional_sign_plan"

    def get_list_queryset(self):
        return prefetch_replacements(additional_sign_plan_get_current())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        additional_sign_plan_soft_delete(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to AdditionalSign Plan",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(AdditionalSignPlanFileSerializer)},
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
        summary="Delete single file from AdditionalSign Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from AdditionalSign Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: AdditionalSignPlanFileSerializer},
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
    create=extend_schema(summary="Create new AdditionalSign Real"),
    list=extend_schema(summary="Retrieve all AdditionalSign Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single AdditionalSign Real"),
    update=extend_schema(summary="Update single AdditionalSign Real"),
    partial_update=extend_schema(summary="Partially update single AdditionalSign Real"),
    destroy=extend_schema(summary="Soft-delete single AdditionalSign Real"),
)
class AdditionalSignRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": AdditionalSignRealSerializer,
        "geojson": AdditionalSignRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = (
        AdditionalSignReal.objects.active()
        .prefetch_related("operations")
        .prefetch_related("operations__operation_type")
        .select_related("additional_sign_plan__plan")
    )
    filterset_class = AdditionalSignRealFilterSet
    file_queryset = AdditionalSignRealFile.objects.all()
    file_serializer = AdditionalSignRealFileSerializer
    file_relation = "additional_sign_real"

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to AdditionalSign Real",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(AdditionalSignRealFileSerializer)},
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
        summary="Delete single file from AdditionalSign Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from AdditionalSign Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: AdditionalSignRealFileSerializer},
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
    create=extend_schema(summary="Add a new operation to an additional sign real"),
    list=extend_schema(summary="Retrieve all operations of an additional sign real"),
    retrieve=extend_schema(summary="Retrieve an operation of an additional sign real"),
    update=extend_schema(summary="Update an operation of an additional sign real"),
    partial_update=extend_schema(summary="Partially update an operation of an additional sign real"),
    destroy=extend_schema(summary="Delete an operation of an additional sign real"),
)
class AdditionalSignRealOperationViewSet(OperationViewSet):
    serializer_class = AdditionalSignRealOperationSerializer
    queryset = AdditionalSignRealOperation.objects.all()
    filterset_class = AdditionalSignRealOperationFilterSet
