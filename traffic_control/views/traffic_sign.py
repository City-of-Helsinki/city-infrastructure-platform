from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
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
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new TrafficSign Code"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all TrafficSign Codes"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single TrafficSign Code"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single TrafficSign Code"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single TrafficSign Code"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Delete single TrafficSign Code"),
)
class TrafficControlDeviceTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = TrafficControlDeviceTypeSerializer
    queryset = TrafficControlDeviceType.objects.all()
    filterset_class = TrafficControlDeviceTypeFilterSet


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new TrafficSign Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all TrafficSign Plans",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single TrafficSign Plan"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single TrafficSign Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single TrafficSign Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single TrafficSign Plan"),
)
class TrafficSignPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignPlanSerializer,
        "geojson": TrafficSignPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficSignPlan.objects.active()
    filterset_class = TrafficSignPlanFilterSet
    file_queryset = TrafficSignPlanFile.objects.all()
    file_serializer = TrafficSignPlanFileSerializer
    file_relation = "traffic_sign_plan"

    @extend_schema(
        methods="post",
        description="Add one or more files to TrafficSign Plan",
        request=MultiFileUploadSchema,
        responses={200: TrafficSignPlanFileSerializer(many=True)},
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
        description="Delete single file from TrafficSign Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from TrafficSign Plan",
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new TrafficSign Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all TrafficSign Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single TrafficSign Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single TrafficSign Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single TrafficSign Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single TrafficSign Real"),
)
class TrafficSignRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = TrafficSignReal.objects.active()
    filterset_class = TrafficSignRealFilterSet
    file_queryset = TrafficSignRealFile.objects.all()
    file_serializer = TrafficSignRealFileSerializer
    file_relation = "traffic_sign_real"

    @extend_schema(
        methods="post",
        description="Add one or more files to TrafficSign Real",
        request=MultiFileUploadSchema,
        responses={200: TrafficSignRealFileSerializer(many=True)},
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
        description="Delete single file from TrafficSign Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from TrafficSign Real",
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


class TrafficSignRealOperationViewSet(OperationViewSet):
    serializer_class = TrafficSignRealOperationSerializer
    queryset = TrafficSignRealOperation.objects.all()
    filterset_class = TrafficSignRealOperationFilterSet
