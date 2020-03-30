from django.core import exceptions
from django.utils.translation import ugettext_lazy as _  # NOQA
from django_filters.rest_framework import DjangoFilterBackend
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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class BarrierRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": BarrierRealSerializer,
        "geojson": BarrierRealGeoJSONSerializer,
    }
    queryset = BarrierReal.objects.active()
    filterset_class = BarrierRealFilterSet


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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class MountRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": MountRealSerializer,
        "geojson": MountRealGeoJSONSerializer,
    }
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.active()
    filterset_class = MountRealFilterSet


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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class RoadMarkingRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    queryset = RoadMarkingReal.objects.active()
    filterset_class = RoadMarkingRealFilterSet


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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class SignpostRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": SignpostRealSerializer,
        "geojson": SignpostRealGeoJSONSerializer,
    }
    queryset = SignpostReal.objects.active()
    filterset_class = SignpostRealFilterSet


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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class TrafficLightRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    queryset = TrafficLightReal.objects.active()
    filterset_class = TrafficLightRealFilterSet


class TrafficSignCodeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = TrafficSignCodeSerializer
    queryset = TrafficSignCode.objects.all()
    filterset_class = TrafficSignCodeFilterSet


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

    @swagger_auto_schema(method="delete", request_body=None, responses={204: ""})
    @swagger_auto_schema(
        method="patch",
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


class TrafficSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    queryset = TrafficSignReal.objects.active()
    filterset_class = TrafficSignRealFilterSet


class PortalTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["structure", "build_type", "model"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PortalTypeSerializer
    queryset = PortalType.objects.all()
    filterset_class = PortalTypeFilterSet
