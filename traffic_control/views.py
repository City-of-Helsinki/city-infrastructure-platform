from django.core import exceptions
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _  # NOQA
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from traffic_control.filters import (
    BarrierPlanFilterSet,
    BarrierRealFilterSet,
    MountPlanFilterSet,
    MountRealFilterSet,
    PortalTypeFilterSet,
    RoadMarkingPlanFilterSet,
    RoadMarkingRealFilterSet,
    SignpostPlanFilterSet,
    SignpostRealFilterSet,
    TrafficLightPlanFilterSet,
    TrafficLightRealFilterSet,
    TrafficSignCodeFilterSet,
    TrafficSignPlanFilterSet,
    TrafficSignRealFilterSet,
)
from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
)
from traffic_control.models.mount import MountPlanFile
from traffic_control.models.road_marking import RoadMarkingPlanFile
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers import (
    BarrierPlanFileSerializer,
    BarrierPlanGeoJSONSerializer,
    BarrierPlanPostFileSerializer,
    BarrierPlanSerializer,
    BarrierRealGeoJSONSerializer,
    BarrierRealSerializer,
    MountPlanFileSerializer,
    MountPlanGeoJSONSerializer,
    MountPlanPostFileSerializer,
    MountPlanSerializer,
    MountRealGeoJSONSerializer,
    MountRealSerializer,
    PortalTypeSerializer,
    RoadMarkingPlanFileSerializer,
    RoadMarkingPlanGeoJSONSerializer,
    RoadMarkingPlanPostFileSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingRealGeoJSONSerializer,
    RoadMarkingRealSerializer,
    SignpostPlanFileSerializer,
    SignpostPlanGeoJSONSerializer,
    SignpostPlanPostFileSerializer,
    SignpostPlanSerializer,
    SignpostRealGeoJSONSerializer,
    SignpostRealSerializer,
    TrafficLightPlanFileSerializer,
    TrafficLightPlanGeoJSONSerializer,
    TrafficLightPlanPostFileSerializer,
    TrafficLightPlanSerializer,
    TrafficLightRealGeoJSONSerializer,
    TrafficLightRealSerializer,
    TrafficSignCodeSerializer,
    TrafficSignPlanFileSerializer,
    TrafficSignPlanGeoJSONSerializer,
    TrafficSignPlanPostFileSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealGeoJSONSerializer,
    TrafficSignRealSerializer,
)

location_parameter = openapi.Parameter(
    "location",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    description="Location (2D or 3D) to search from in WKT-format (EPSG:3879)",
    format="WKT",
)


class TrafficControlViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_classes = {}

    def get_serializer_class(self):
        geo_format = self.request.query_params.get("geo_format")
        if geo_format == "geojson":
            return self.serializer_classes.get("geojson")
        return self.serializer_classes.get("default")


class FileUploadViews(GenericViewSet):
    file_queryset = None
    file_serializer = None
    file_relation = None

    def get_file_relation(self):
        return self.file_relation

    def get_file_serializer(self):
        return self.file_serializer

    @action(
        methods=("POST",),
        detail=True,
        url_path="files",
        parser_classes=(MultiPartParser,),
    )
    def post_file(self, request, *args, **kwargs):
        obj = self.get_object()

        data = request.data.dict()
        data[self.get_file_relation()] = obj.id

        serializer_class = self.get_file_serializer()
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(
        methods=("PATCH", "DELETE",),
        detail=True,
        url_path="files/(?P<file_pk>[^/.]+)",
        parser_classes=(MultiPartParser,),
    )
    def change_file(self, request, file_pk, *args, **kwargs):
        if request.method == "DELETE":
            try:
                instance = self.file_queryset.get(id=file_pk)
            except exceptions.ObjectDoesNotExist:
                return Response(
                    {"detail": _("File not found.")}, status=status.HTTP_404_NOT_FOUND
                )

            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == "PATCH":
            instance = self.file_queryset.get(id=file_pk)
            serializer_class = self.get_file_serializer()
            serializer = serializer_class(
                instance=instance, data=request.data, partial=True
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
        operation_description="Add single file to Mount Plan",
        request_body=MountPlanPostFileSerializer,
        responses={200: MountPlanFileSerializer},
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
        operation_description="Delete single file from Mount Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Mount Plan",
        request_body=MountPlanPostFileSerializer,
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
class MountRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": MountRealSerializer,
        "geojson": MountRealGeoJSONSerializer,
    }
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.active()
    filterset_class = MountRealFilterSet


@method_decorator(
    name="create",
    decorator=swagger_auto_schema(operation_description="Create new RoadMarking Plan"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all RoadMarking Plans",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single RoadMarking Plan"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single RoadMarking Plan"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single RoadMarking Plan"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single RoadMarking Plan"
    ),
)
class RoadMarkingPlanViewSet(TrafficControlViewSet, FileUploadViews):
    serializer_classes = {
        "default": RoadMarkingPlanSerializer,
        "geojson": RoadMarkingPlanGeoJSONSerializer,
    }
    queryset = RoadMarkingPlan.objects.active()
    filterset_class = RoadMarkingPlanFilterSet
    file_queryset = RoadMarkingPlanFile.objects.all()
    file_serializer = RoadMarkingPlanFileSerializer
    file_relation = "road_marking_plan"

    @swagger_auto_schema(
        method="post",
        operation_description="Add single file to RoadMarking Plan",
        request_body=RoadMarkingPlanPostFileSerializer,
        responses={200: RoadMarkingPlanFileSerializer},
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
        operation_description="Delete single file from RoadMarking Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from RoadMarking Plan",
        request_body=RoadMarkingPlanPostFileSerializer,
        responses={200: RoadMarkingPlanFileSerializer},
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
    decorator=swagger_auto_schema(operation_description="Create new RoadMarking Real"),
)
@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="Retrieve all RoadMarking Reals",
        manual_parameters=[location_parameter],
    ),
)
@method_decorator(
    name="retrieve",
    decorator=swagger_auto_schema(
        operation_description="Retrieve single RoadMarking Real"
    ),
)
@method_decorator(
    name="update",
    decorator=swagger_auto_schema(
        operation_description="Update single RoadMarking Real"
    ),
)
@method_decorator(
    name="partial_update",
    decorator=swagger_auto_schema(
        operation_description="Partially update single RoadMarking Real"
    ),
)
@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(
        operation_description="Soft-delete single RoadMarking Real"
    ),
)
class RoadMarkingRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    queryset = RoadMarkingReal.objects.active()
    filterset_class = RoadMarkingRealFilterSet


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
        operation_description="Add single file to Signpost Plan",
        request_body=SignpostPlanPostFileSerializer,
        responses={200: SignpostPlanFileSerializer},
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
        operation_description="Delete single file from Signpost Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from Signpost Plan",
        request_body=SignpostPlanPostFileSerializer,
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
class SignpostRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": SignpostRealSerializer,
        "geojson": SignpostRealGeoJSONSerializer,
    }
    queryset = SignpostReal.objects.active()
    filterset_class = SignpostRealFilterSet


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
        operation_description="Add single file to TrafficLight Plan",
        request_body=TrafficLightPlanPostFileSerializer,
        responses={200: TrafficLightPlanFileSerializer},
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
        operation_description="Delete single file from TrafficLight Plan",
        request_body=None,
        responses={204: ""},
    )
    @swagger_auto_schema(
        method="patch",
        operation_description="Update single file from TrafficLight Plan",
        request_body=TrafficLightPlanPostFileSerializer,
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
class TrafficLightRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    queryset = TrafficLightReal.objects.active()
    filterset_class = TrafficLightRealFilterSet


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
    def post_file(self, request, *args, **kwargs):
        return super().post_file(request, *args, **kwargs)

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
class TrafficSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    queryset = TrafficSignReal.objects.active()
    filterset_class = TrafficSignRealFilterSet


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
