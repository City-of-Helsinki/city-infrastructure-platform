from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet

from ..filters import MountPlanFilterSet, MountRealFilterSet, PortalTypeFilterSet
from ..models import MountPlan, MountPlanFile, MountReal, MountRealFile, PortalType
from ..permissions import IsAdminUserOrReadOnly
from ..schema import (
    file_uuid_parameter,
    FileUploadSchema,
    MultiFileUploadSchema,
)
from ..serializers import (
    MountPlanFileSerializer,
    MountPlanGeoJSONSerializer,
    MountPlanSerializer,
    MountRealFileSerializer,
    MountRealGeoJSONSerializer,
    MountRealSerializer,
    PortalTypeSerializer,
)
from ._common import FileUploadViews, location_parameter, TrafficControlViewSet

__all__ = ("MountPlanViewSet", "MountRealViewSet", "PortalTypeViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Mount Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Mount Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Mount Plan"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Mount Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Mount Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Mount Plan"
    ),
)
class MountPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": MountPlanSerializer,
        "geojson": MountPlanGeoJSONSerializer,
    }
    queryset = MountPlan.objects.active()
    filterset_class = MountPlanFilterSet
    file_queryset = MountPlanFile.objects.all()
    file_serializer = MountPlanFileSerializer
    file_relation = "mount_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Mount Plan",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Mount Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Mount Plan",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: MountPlanFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Mount Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Mount Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Mount Real"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Mount Real"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Mount Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Mount Real"
    ),
)
class MountRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": MountRealSerializer,
        "geojson": MountRealGeoJSONSerializer,
    }
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.active()
    filterset_class = MountRealFilterSet
    file_queryset = MountRealFile.objects.all()
    file_serializer = MountRealFileSerializer
    file_relation = "mount_real"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Mount Real",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Mount Real",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Mount Real",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: MountRealFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new PortalType"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all PortalTypes"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single PortalType"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single PortalType"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single PortalType"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(operation_description="Delete single PortalType"),
)
class PortalTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["structure", "build_type", "model"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PortalTypeSerializer
    queryset = PortalType.objects.all()
    filterset_class = PortalTypeFilterSet
