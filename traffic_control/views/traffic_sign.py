from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import ModelViewSet

from ..filters import (
    TrafficSignCodeFilterSet,
    TrafficSignPlanFilterSet,
    TrafficSignRealFilterSet,
)
from ..models import (
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from ..permissions import IsAdminUserOrReadOnly
from ..serializers import (
    TrafficSignCodeSerializer,
    TrafficSignPlanFileSerializer,
    TrafficSignPlanGeoJSONSerializer,
    TrafficSignPlanPostFileSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealFileSerializer,
    TrafficSignRealGeoJSONSerializer,
    TrafficSignRealPostFileSerializer,
    TrafficSignRealSerializer,
)
from ._common import FileUploadViews, location_parameter, TrafficControlViewSet

__all__ = ("TrafficSignCodeViewSet", "TrafficSignPlanViewSet", "TrafficSignRealViewSet")


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new TrafficSign Code"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all TrafficSign Codes"
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single TrafficSign Code"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single TrafficSign Code"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single TrafficSign Code"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Delete single TrafficSign Code"
    ),
)
class TrafficSignCodeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = TrafficSignCodeSerializer
    queryset = TrafficSignCode.objects.all()
    filterset_class = TrafficSignCodeFilterSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new TrafficSign Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all TrafficSign Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single TrafficSign Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single TrafficSign Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single TrafficSign Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single TrafficSign Plan"
    ),
)
class TrafficSignPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignPlanSerializer,
        "geojson": TrafficSignPlanGeoJSONSerializer,
    }
    queryset = TrafficSignPlan.objects.active()
    filterset_class = TrafficSignPlanFilterSet
    file_queryset = TrafficSignPlanFile.objects.all()
    file_serializer = TrafficSignPlanFileSerializer
    file_relation = "traffic_sign_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add single file to TrafficSign Plan",
        request_body=TrafficSignPlanPostFileSerializer,
        responses={200: TrafficSignPlanFileSerializer},
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
        operation_description="Delete single file from TrafficSign Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from TrafficSign Plan",
        request_body=TrafficSignPlanPostFileSerializer,
        responses={200: TrafficSignPlanFileSerializer},
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
    decorator=swagger_auto_schema(operation_description="Create new TrafficSign Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all TrafficSign Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single TrafficSign Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single TrafficSign Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single TrafficSign Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single TrafficSign Real"
    ),
)
class TrafficSignRealViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    queryset = TrafficSignReal.objects.active()
    filterset_class = TrafficSignRealFilterSet
    file_queryset = TrafficSignRealFile.objects.all()
    file_serializer = TrafficSignRealFileSerializer
    file_relation = "traffic_sign_real"

    @swagger_auto_schema(
        method="post",
        operation_description="Add single file to TrafficSign Real",
        request_body=TrafficSignRealPostFileSerializer,
        responses={200: TrafficSignRealFileSerializer},
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
        operation_description="Delete single file from TrafficSign Real",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from TrafficSign Real",
        request_body=TrafficSignRealPostFileSerializer,
        responses={200: TrafficSignRealFileSerializer},
    )
    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        return super().change_file(request, file_pk, *args, **kwargs)
