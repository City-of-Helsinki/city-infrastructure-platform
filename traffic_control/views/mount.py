from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet

from traffic_control.filters import (
    MountPlanFilterSet,
    MountRealFilterSet,
    MountRealOperationFilterSet,
    MountTypeFilterSet,
    PortalTypeFilterSet,
)
from traffic_control.models import (
    MountPlan,
    MountPlanFile,
    MountReal,
    MountRealFile,
    MountRealOperation,
    MountType,
    PortalType,
)
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.schema import (
    file_create_serializer,
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.mount import (
    MountPlanFileSerializer,
    MountPlanGeoJSONSerializer,
    MountPlanSerializer,
    MountRealFileSerializer,
    MountRealGeoJSONSerializer,
    MountRealOperationSerializer,
    MountRealSerializer,
    MountTypeSerializer,
    PortalTypeSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("MountPlanViewSet", "MountRealViewSet", "PortalTypeViewSet")


@extend_schema_view(
    create=extend_schema(summary="Create new Mount Plan"),
    list=extend_schema(summary="Retrieve all Mount Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Mount Plan"),
    update=extend_schema(summary="Update single Mount Plan"),
    partial_update=extend_schema(summary="Partially update single Mount Plan"),
    destroy=extend_schema(summary="Soft-delete single Mount Plan"),
)
class MountPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": MountPlanSerializer,
        "geojson": MountPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = MountPlan.objects.active()
    filterset_class = MountPlanFilterSet
    file_queryset = MountPlanFile.objects.all()
    file_serializer = MountPlanFileSerializer
    file_relation = "mount_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Mount Plan",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(MountPlanFileSerializer)},
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
        summary="Delete single file from Mount Plan",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Mount Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: MountPlanFileSerializer},
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
    create=extend_schema(summary="Create new Mount Real"),
    list=extend_schema(summary="Retrieve all Mount Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Mount Real"),
    update=extend_schema(summary="Update single Mount Real"),
    partial_update=extend_schema(summary="Partially update single Mount Real"),
    destroy=extend_schema(summary="Soft-delete single Mount Real"),
)
class MountRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": MountRealSerializer,
        "geojson": MountRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.active()
    filterset_class = MountRealFilterSet
    file_queryset = MountRealFile.objects.all()
    file_serializer = MountRealFileSerializer
    file_relation = "mount_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Mount Real",
        request=MultiFileUploadSchema,
        responses={200: file_create_serializer(MountRealFileSerializer)},
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
        summary="Delete single file from Mount Real",
        parameters=[file_uuid_parameter],
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Mount Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: MountRealFileSerializer},
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
    create=extend_schema(summary="Create new PortalType"),
    list=extend_schema(summary="Retrieve all PortalTypes"),
    retrieve=extend_schema(summary="Retrieve single PortalType"),
    update=extend_schema(summary="Update single PortalType"),
    partial_update=extend_schema(summary="Partially update single PortalType"),
    destroy=extend_schema(summary="Delete single PortalType"),
)
class PortalTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["structure", "build_type", "model"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PortalTypeSerializer
    queryset = PortalType.objects.all()
    filterset_class = PortalTypeFilterSet


@extend_schema_view(
    create=extend_schema(summary="Create new MountType"),
    list=extend_schema(summary="Retrieve all MountTypes"),
    retrieve=extend_schema(summary="Retrieve single MountType"),
    update=extend_schema(summary="Update single MountType"),
    partial_update=extend_schema(summary="Partially update single MountType"),
    destroy=extend_schema(summary="Delete single MountType"),
)
class MountTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code", "description"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = MountTypeSerializer
    queryset = MountType.objects.all()
    filterset_class = MountTypeFilterSet


@extend_schema_view(
    create=extend_schema(summary="Add a new operation to a mount real"),
    list=extend_schema(summary="Retrieve all operations of a mount real"),
    retrieve=extend_schema(summary="Retrieve an operation of a mount real"),
    update=extend_schema(summary="Update an operation of a mount real"),
    partial_update=extend_schema(summary="Partially update an operation of a mount real"),
    destroy=extend_schema(summary="Delete an operation of a mount real"),
)
class MountRealOperationViewSet(OperationViewSet):
    serializer_class = MountRealOperationSerializer
    queryset = MountRealOperation.objects.all()
    filterset_class = MountRealOperationFilterSet
