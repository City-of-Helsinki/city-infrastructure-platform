from django.core import exceptions
from django.utils.translation import ugettext_lazy as _  # NOQA
from django_filters.rest_framework import DjangoFilterBackend
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
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.permissions import IsAdminUserOrReadOnly
from traffic_control.serializers import (
    BarrierPlanGeoJSONSerializer,
    BarrierPlanSerializer,
    BarrierPlanUploadSerializer,
    BarrierRealGeoJSONSerializer,
    BarrierRealSerializer,
    MountPlanGeoJSONSerializer,
    MountPlanSerializer,
    MountPlanUploadSerializer,
    MountRealGeoJSONSerializer,
    MountRealSerializer,
    PortalTypeSerializer,
    RoadMarkingPlanGeoJSONSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingPlanUploadSerializer,
    RoadMarkingRealGeoJSONSerializer,
    RoadMarkingRealSerializer,
    SignpostPlanGeoJSONSerializer,
    SignpostPlanSerializer,
    SignpostPlanUploadSerializer,
    SignpostRealGeoJSONSerializer,
    SignpostRealSerializer,
    TrafficLightPlanGeoJSONSerializer,
    TrafficLightPlanSerializer,
    TrafficLightPlanUploadSerializer,
    TrafficLightRealGeoJSONSerializer,
    TrafficLightRealSerializer,
    TrafficSignCodeSerializer,
    TrafficSignPlanGeoJSONSerializer,
    TrafficSignPlanSerializer,
    TrafficSignPlanUploadSerializer,
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
            return Response(status=status.HTTP_200_OK)

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


class BarrierPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": BarrierPlanSerializer,
        "geojson": BarrierPlanGeoJSONSerializer,
    }
    queryset = BarrierPlan.objects.all()
    filterset_class = BarrierPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=BarrierPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class BarrierRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": BarrierRealSerializer,
        "geojson": BarrierRealGeoJSONSerializer,
    }
    queryset = BarrierReal.objects.all()
    filterset_class = BarrierRealFilterSet


class MountPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": MountPlanSerializer,
        "geojson": MountPlanGeoJSONSerializer,
    }
    serializer_class = MountPlanSerializer
    queryset = MountPlan.objects.all()
    filterset_class = MountPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=MountPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class MountRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": MountRealSerializer,
        "geojson": MountRealGeoJSONSerializer,
    }
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.all()
    filterset_class = MountRealFilterSet


class RoadMarkingPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": RoadMarkingPlanSerializer,
        "geojson": RoadMarkingPlanGeoJSONSerializer,
    }
    queryset = RoadMarkingPlan.objects.all()
    filterset_class = RoadMarkingPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=RoadMarkingPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class RoadMarkingRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": RoadMarkingRealSerializer,
        "geojson": RoadMarkingRealGeoJSONSerializer,
    }
    queryset = RoadMarkingReal.objects.all()
    filterset_class = RoadMarkingRealFilterSet


class SignpostPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": SignpostPlanSerializer,
        "geojson": SignpostPlanGeoJSONSerializer,
    }
    queryset = SignpostPlan.objects.all()
    filterset_class = SignpostPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=SignpostPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class SignpostRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": SignpostRealSerializer,
        "geojson": SignpostRealGeoJSONSerializer,
    }
    queryset = SignpostReal.objects.all()
    filterset_class = SignpostRealFilterSet


class TrafficLightPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficLightPlanSerializer,
        "geojson": TrafficLightPlanGeoJSONSerializer,
    }
    queryset = TrafficLightPlan.objects.all()
    filterset_class = TrafficLightPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=TrafficLightPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class TrafficLightRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficLightRealSerializer,
        "geojson": TrafficLightRealGeoJSONSerializer,
    }
    queryset = TrafficLightReal.objects.all()
    filterset_class = TrafficLightRealFilterSet


class TrafficSignCodeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["code"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = TrafficSignCodeSerializer
    queryset = TrafficSignCode.objects.all()
    filterset_class = TrafficSignCodeFilterSet


class TrafficSignPlanViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficSignPlanSerializer,
        "geojson": TrafficSignPlanGeoJSONSerializer,
    }
    queryset = TrafficSignPlan.objects.all()
    filterset_class = TrafficSignPlanFilterSet

    @action(
        methods=("PUT",),
        detail=True,
        parser_classes=(MultiPartParser,),
        serializer_class=TrafficSignPlanUploadSerializer,
    )
    def upload_plan(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class TrafficSignRealViewSet(TrafficControlViewSet):
    serializer_classes = {
        "default": TrafficSignRealSerializer,
        "geojson": TrafficSignRealGeoJSONSerializer,
    }
    queryset = TrafficSignReal.objects.all()
    filterset_class = TrafficSignRealFilterSet


class PortalTypeViewSet(ModelViewSet):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["structure", "build_type", "model"]
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = PortalTypeSerializer
    queryset = PortalType.objects.all()
    filterset_class = PortalTypeFilterSet
