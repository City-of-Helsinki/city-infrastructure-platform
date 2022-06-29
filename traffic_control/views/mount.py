from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
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
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Mount Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all Mount Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Mount Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Mount Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Mount Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single Mount Plan"),
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
        methods="post",
        description="Add one or more files to Mount Plan",
        request=MultiFileUploadSchema,
        responses={200: MountPlanFileSerializer(many=True)},
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
        description="Delete single file from Mount Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Mount Plan",
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Mount Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all Mount Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Mount Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Mount Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Mount Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single Mount Real"),
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
        methods="post",
        description="Add one or more files to Mount Real",
        request=MultiFileUploadSchema,
        responses={200: MountRealFileSerializer(many=True)},
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
        description="Delete single file from Mount Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Mount Real",
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new PortalType"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all PortalTypes"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single PortalType"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single PortalType"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single PortalType"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single PortalType"),
)
class PortalTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["structure", "build_type", "model"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PortalTypeSerializer
    queryset = PortalType.objects.all()
    filterset_class = PortalTypeFilterSet


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new MountType"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all MountTypes"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single MountType"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single MountType"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single MountType"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single MountType"),
)
class MountTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code", "description"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = MountTypeSerializer
    queryset = MountType.objects.all()
    filterset_class = MountTypeFilterSet


class MountRealOperationViewSet(OperationViewSet):
    serializer_class = MountRealOperationSerializer
    queryset = MountRealOperation.objects.all()
    filterset_class = MountRealOperationFilterSet
