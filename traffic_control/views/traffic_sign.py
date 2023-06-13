from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import (
    TrafficControlDeviceTypeFilterSet,
    TrafficSignPlanFilterSet,
    TrafficSignRealFilterSet,
    TrafficSignRealOperationFilterSet,
)
from traffic_control.models import (
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
    TrafficSignRealOperation,
)
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.schema import (
    file_create_serializer,
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.common import TrafficControlDeviceTypeSerializer
from traffic_control.serializers.traffic_sign import (
    TrafficSignPlanFileSerializer,
    TrafficSignPlanGeoJSONSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealFileSerializer,
    TrafficSignRealGeoJSONSerializer,
    TrafficSignRealOperationSerializer,
    TrafficSignRealSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = (
    "TrafficControlDeviceTypeViewSet",
    "TrafficSignPlanViewSet",
    "TrafficSignRealViewSet",
)


@extend_schema_view(
    create=extend_schema(summary="Create new TrafficSign Code"),
    list=extend_schema(summary="Retrieve all TrafficSign Codes"),
    retrieve=extend_schema(summary="Retrieve single TrafficSign Code"),
    update=extend_schema(summary="Update single TrafficSign Code"),
    partial_update=extend_schema(summary="Partially update single TrafficSign Code"),
    destroy=extend_schema(summary="Delete single TrafficSign Code"),
)
class TrafficControlDeviceTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = TrafficControlDeviceTypeSerializer
    queryset = TrafficControlDeviceType.objects.all()
    filterset_class = TrafficControlDeviceTypeFilterSet


@extend_schema_view(
    create=extend_schema(summary="Create new TrafficSign Plan"),
    list=extend_schema(summary="Retrieve all TrafficSign Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single TrafficSign Plan"),
    update=extend_schema(summary="Update single TrafficSign Plan"),
    partial_update=extend_schema(summary="Partially update single TrafficSign Plan"),
    destroy=extend_schema(summary="Soft-delete single TrafficSign Plan"),
)
class TrafficSignPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignPlanSerializer,
        "geojson": TrafficSignPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficSignPlan.objects.active().prefetch_related("files")
    filterset_class = TrafficSignPlanFilterSet
    file_queryset = TrafficSignPlanFile.objects.all()
    file_serializer = TrafficSignPlanFileSerializer
    file_relation = "traffic_sign_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to TrafficSign Plan",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(TrafficSignPlanFileSerializer)},
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
        summary="Delete single file from TrafficSign Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from TrafficSign Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: TrafficSignPlanFileSerializer},
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
    create=extend_schema(summary="Create new TrafficSign Real"),
    list=extend_schema(summary="Retrieve all TrafficSign Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single TrafficSign Real"),
    update=extend_schema(summary="Update single TrafficSign Real"),
    partial_update=extend_schema(summary="Partially update single TrafficSign Real"),
    destroy=extend_schema(summary="Soft-delete single TrafficSign Real"),
)
class TrafficSignRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = (
        TrafficSignReal.objects.active()
        .prefetch_related("files")
        .prefetch_related("operations")
        .prefetch_related("operations__operation_type")
    )
    filterset_class = TrafficSignRealFilterSet
    file_queryset = TrafficSignRealFile.objects.all()
    file_serializer = TrafficSignRealFileSerializer
    file_relation = "traffic_sign_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to TrafficSign Real",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(TrafficSignRealFileSerializer)},
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
        summary="Delete single file from TrafficSign Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from TrafficSign Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: TrafficSignRealFileSerializer},
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
    create=extend_schema(summary="Add a new operation to a traffic sign real"),
    list=extend_schema(summary="Retrieve all operations of a traffic sign real"),
    retrieve=extend_schema(summary="Retrieve an operation of a traffic sign real"),
    update=extend_schema(summary="Update an operation of a traffic sign real"),
    partial_update=extend_schema(summary="Partially update an operation of a traffic sign real"),
    destroy=extend_schema(summary="Delete an operation of a traffic sign real"),
)
class TrafficSignRealOperationViewSet(OperationViewSet):
    serializer_class = TrafficSignRealOperationSerializer
    queryset = TrafficSignRealOperation.objects.all()
    filterset_class = TrafficSignRealOperationFilterSet
