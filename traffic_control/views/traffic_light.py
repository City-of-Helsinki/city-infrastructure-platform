from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from ..filters import TrafficLightPlanFilterSet, TrafficLightRealFilterSet
from ..models import (
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
)
from ..schema import (
    file_uuid_parameter,
    FileUploadSchema,
    location_parameter,
    MultiFileUploadSchema,
)
from ..serializers.traffic_light import (
    TrafficLightPlanFileSerializer,
    TrafficLightPlanGeoJSONSerializer,
    TrafficLightPlanSerializer,
    TrafficLightRealFileSerializer,
    TrafficLightRealGeoJSONSerializer,
    TrafficLightRealSerializer,
)
from ._common import FileUploadViews, TrafficControlViewSet

__all__ = ("TrafficLightPlanViewSet", "TrafficLightRealViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new TrafficLight Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all TrafficLight Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single TrafficLight Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single TrafficLight Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single TrafficLight Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single TrafficLight Plan"
    ),
)
class TrafficLightPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightPlanSerializer,
        "geojson": TrafficLightPlanGeoJSONSerializer,
    }
    queryset = TrafficLightPlan.objects.active()
    filterset_class = TrafficLightPlanFilterSet
    file_queryset = TrafficLightPlanFile.objects.all()
    file_serializer = TrafficLightPlanFileSerializer
    file_relation = "traffic_light_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to TrafficLight Plan",
        request_body=MultiFileUploadSchema,
        responses={200: TrafficLightPlanFileSerializer(many=True)},
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
        operation_description="Delete single file from TrafficLight Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from TrafficLight Plan",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: TrafficLightPlanFileSerializer},
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
    decorator=swagger_auto_schema(operation_description="Create new TrafficLight Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all TrafficLight Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single TrafficLight Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single TrafficLight Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single TrafficLight Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single TrafficLight Real"
    ),
)
class TrafficLightRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    queryset = TrafficLightReal.objects.active()
    filterset_class = TrafficLightRealFilterSet
    file_queryset = TrafficLightRealFile.objects.all()
    file_serializer = TrafficLightRealFileSerializer
    file_relation = "traffic_light_real"

    @swagger_auto_schema(
        method="post",
        operation_description="Add one or more files to TrafficLight Real",
        request_body=MultiFileUploadSchema,
        responses={200: TrafficLightRealFileSerializer(many=True)},
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
        operation_description="Delete single file from TrafficLight Real",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from TrafficLight Real",
        manual_parameters=[file_uuid_parameter],
        request_body=FileUploadSchema,
        responses={200: TrafficLightRealFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)
