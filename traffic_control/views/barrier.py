from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from traffic_control.filters import BarrierPlanFilterSet, BarrierRealFilterSet, BarrierRealOperationFilterSet
from traffic_control.models import BarrierPlan, BarrierPlanFile, BarrierReal, BarrierRealFile, BarrierRealOperation
from traffic_control.schema import (
    file_uuid_parameter,
    FileUploadSchema,
    location_search_parameter,
    MultiFileUploadSchema,
)
from traffic_control.serializers.barrier import (
    BarrierPlanFileSerializer,
    BarrierPlanGeoJSONSerializer,
    BarrierPlanSerializer,
    BarrierRealFileSerializer,
    BarrierRealGeoJSONSerializer,
    BarrierRealOperationSerializer,
    BarrierRealSerializer,
)
from traffic_control.views._common import (
    FileUploadViews,
    OperationViewSet,
    ResponsibleEntityPermission,
    TrafficControlViewSet,
)

__all__ = ("BarrierPlanViewSet", "BarrierRealViewSet")


@extend_schema_view(
    create=extend_schema(summary="Create new Barrier Plan"),
    list=extend_schema(summary="Retrieve all Barrier Plans", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Barrier Plan"),
    update=extend_schema(summary="Update single Barrier Plan"),
    partial_update=extend_schema(summary="Partially update single Barrier Plan"),
    destroy=extend_schema(summary="Soft-delete single Barrier Plan"),
)
class BarrierPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": BarrierPlanSerializer,
        "geojson": BarrierPlanGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = BarrierPlan.objects.active()
    filterset_class = BarrierPlanFilterSet
    file_queryset = BarrierPlanFile.objects.all()
    file_serializer = BarrierPlanFileSerializer
    file_relation = "barrier_plan"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Barrier Plan",
        request=MultiFileUploadSchema,
        responses={200: BarrierPlanFileSerializer(many=True)},
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
        summary="Delete single file from Barrier Plan",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Barrier Plan",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: BarrierPlanFileSerializer},
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
    create=extend_schema(summary="Create new Barrier Real"),
    list=extend_schema(summary="Retrieve all Barrier Reals", parameters=[location_search_parameter]),
    retrieve=extend_schema(summary="Retrieve single Barrier Real"),
    update=extend_schema(summary="Update single Barrier Real"),
    partial_update=extend_schema(summary="Partially update single Barrier Real"),
    destroy=extend_schema(summary="Soft-delete single Barrier Real"),
)
class BarrierRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": BarrierRealSerializer,
        "geojson": BarrierRealGeoJSONSerializer,
    }
    permission_classes = [ResponsibleEntityPermission, *TrafficControlViewSet.permission_classes]
    queryset = BarrierReal.objects.active()
    filterset_class = BarrierRealFilterSet
    file_queryset = BarrierRealFile.objects.all()
    file_serializer = BarrierRealFileSerializer
    file_relation = "barrier_real"

    @extend_schema(
        methods=("post",),
        summary="Add one or more files to Barrier Real",
        request=MultiFileUploadSchema,
        responses={200: BarrierRealFileSerializer(many=True)},
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
        summary="Delete single file from Barrier Real",
        request=None,
        responses={204: ""},
    )
    @extend_schema(
        methods=("patch",),
        summary="Update single file from Barrier Real",
        parameters=[file_uuid_parameter],
        request=FileUploadSchema,
        responses={200: BarrierRealFileSerializer},
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


class BarrierRealOperationViewSet(OperationViewSet):
    serializer_class = BarrierRealOperationSerializer
    queryset = BarrierRealOperation.objects.all()
    filterset_class = BarrierRealOperationFilterSet
