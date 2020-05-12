from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from ..filters import BarrierPlanFilterSet, BarrierRealFilterSet
from ..models import BarrierPlan, BarrierPlanFile, BarrierReal
from ..serializers import (
    BarrierPlanFileSerializer,
    BarrierPlanGeoJSONSerializer,
    BarrierPlanPostFileSerializer,
    BarrierPlanSerializer,
    BarrierRealGeoJSONSerializer,
    BarrierRealSerializer,
)
from ._common import FileUploadViews, location_parameter, TrafficControlViewSet

__all__ = ("BarrierPlanViewSet", "BarrierRealViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new Barrier Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Barrier Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Barrier Plan"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Barrier Plan"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Barrier Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Barrier Plan"
    ),
)
class BarrierPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": BarrierPlanSerializer,
        "geojson": BarrierPlanGeoJSONSerializer,
    }
    queryset = BarrierPlan.objects.active()
    filterset_class = BarrierPlanFilterSet
    file_queryset = BarrierPlanFile.objects.all()
    file_serializer = BarrierPlanFileSerializer
    file_relation = "barrier_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add single file to Barrier Plan",
        request_body=BarrierPlanPostFileSerializer,
        responses={200: BarrierPlanFileSerializer},
    )
    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_file(self, request, *args, **kwargs):
        return super().post_file(request, *args, **kwargs)

    @swagger_auto_schema(
        method="delete",
        operation_description="Delete single file from Barrier Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Barrier Plan",
        request_body=BarrierPlanPostFileSerializer,
        responses={200: BarrierPlanFileSerializer},
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
    decorator=swagger_auto_schema(operation_description="Create new Barrier Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all Barrier Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(operation_description="Retrieve single Barrier Real"),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(operation_description="Update single Barrier Real"),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single Barrier Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single Barrier Real"
    ),
)
class BarrierRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": BarrierRealSerializer,
        "geojson": BarrierRealGeoJSONSerializer,
    }
    queryset = BarrierReal.objects.active()
    filterset_class = BarrierRealFilterSet
