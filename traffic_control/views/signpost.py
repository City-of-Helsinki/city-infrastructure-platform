from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from traffic_control.filters import SignpostPlanFilterSet, SignpostRealFilterSet, SignpostRealOperationFilterSet
from traffic_control.models import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile, SignpostRealOperation
from traffic_control.schema import file_uuid_parameter, FileUploadSchema, location_parameter, MultiFileUploadSchema
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Signpost Plan"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(description="Retrieve all Signpost Plans"),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(
        description="Retrieve single Signpost Plan",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Signpost Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Signpost Plan"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single Signpost Plan"),
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
        methods="post",
        description="Add one or more files to Signpost Plan",
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
        methods="delete",
        description="Delete single file from Signpost Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Signpost Plan",
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


@method_decorator(
    name="create",
    decorator=extend_schema(description="Create new Signpost Real"),
)
@method_decorator(
    name="list",
    decorator=extend_schema(
        description="Retrieve all Signpost Reals",
        parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(description="Retrieve single Signpost Real"),
)
@method_decorator(
    name="update",
    decorator=extend_schema(description="Update single Signpost Real"),
)
@method_decorator(
    name="partial_update",
    decorator=extend_schema(description="Partially update single Signpost Real"),
)
@method_decorator(
    name="destroy",
    decorator=extend_schema(description="Soft-delete single Signpost Real"),
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
        methods="post",
        description="Add one or more files to Signpost Real",
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
        methods="delete",
        description="Delete single file from Signpost Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods="patch",
        description="Update single file from Signpost Real",
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


class SignpostRealOperationViewSet(OperationViewSet):
    serializer_class = SignpostRealOperationSerializer
    queryset = SignpostRealOperation.objects.all()
    filterset_class = SignpostRealOperationFilterSet
