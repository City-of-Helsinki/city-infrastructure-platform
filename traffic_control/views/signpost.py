from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from ..filters import SignpostPlanFilterSet, SignpostRealFilterSet
from ..models import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile
from ..schema import (
    file_uuid_parameter,
    FileUploadSchema,
    location_parameter,
    MultiFileUploadSchema,
)
from ..serializers.signpost import (
    SignpostPlanFileSerializer,
    SignpostPlanGeoJSONSerializer,
    SignpostPlanSerializer,
    SignpostRealFileSerializer,
    SignpostRealGeoJSONSerializer,
    SignpostRealSerializer,
)
from ._common import FileUploadViews, TrafficControlViewSet

__all__ = ("SignpostPlanViewSet", "SignpostRealViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Signpost Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(operation_description="Retrieve all Signpost Plans"),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single Signpost Plan",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Signpost Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Signpost Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Signpost Plan"
    ),
)
class SignpostPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": SignpostPlanSerializer,
        "geojson": SignpostPlanGeoJSONSerializer,
    }
    queryset = SignpostPlan.objects.active()
    filterset_class = SignpostPlanFilterSet
    file_queryset = SignpostPlanFile.objects.all()
    file_serializer = SignpostPlanFileSerializer
    file_relation = "signpost_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Signpost Plan",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Signpost Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Signpost Plan",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: SignpostPlanFileSerializer},
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
    decorator=swagger_auto_schema(operation_description="Create new Signpost Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Signpost Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single Signpost Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Signpost Real"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Signpost Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Signpost Real"
    ),
)
class SignpostRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": SignpostRealSerializer,
        "geojson": SignpostRealGeoJSONSerializer,
    }
    queryset = SignpostReal.objects.active()
    filterset_class = SignpostRealFilterSet
    file_queryset = SignpostRealFile.objects.all()
    file_serializer = SignpostRealFileSerializer
    file_relation = "signpost_real"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to Signpost Real",
        request_body=MultiFileUploadSchema,
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

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Signpost Real",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Signpost Real",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: SignpostRealFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)
