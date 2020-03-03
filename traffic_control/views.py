from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
    BarrierPlanSerializer,
    BarrierPlanUploadSerializer,
    BarrierRealSerializer,
    MountPlanSerializer,
    MountPlanUploadSerializer,
    MountRealSerializer,
    PortalTypeSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingPlanUploadSerializer,
    RoadMarkingRealSerializer,
    SignpostPlanSerializer,
    SignpostPlanUploadSerializer,
    SignpostRealSerializer,
    TrafficLightPlanSerializer,
    TrafficLightPlanUploadSerializer,
    TrafficLightRealSerializer,
    TrafficSignCodeSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealSerializer,
)


class TrafficControlViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]
    permission_classes = [IsAuthenticatedOrReadOnly]


class BarrierPlanViewSet(TrafficControlViewSet):
    serializer_class = BarrierPlanSerializer
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
    serializer_class = BarrierRealSerializer
    queryset = BarrierReal.objects.all()
    filterset_class = BarrierRealFilterSet


class MountPlanViewSet(TrafficControlViewSet):
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
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.all()
    filterset_class = MountRealFilterSet


class RoadMarkingPlanViewSet(TrafficControlViewSet):
    serializer_class = RoadMarkingPlanSerializer
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
    serializer_class = RoadMarkingRealSerializer
    queryset = RoadMarkingReal.objects.all()
    filterset_class = RoadMarkingRealFilterSet


class SignpostPlanViewSet(TrafficControlViewSet):
    serializer_class = SignpostPlanSerializer
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
    serializer_class = SignpostRealSerializer
    queryset = SignpostReal.objects.all()
    filterset_class = SignpostRealFilterSet


class TrafficLightPlanViewSet(TrafficControlViewSet):
    serializer_class = TrafficLightPlanSerializer
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
    serializer_class = TrafficLightRealSerializer
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
    serializer_class = TrafficSignPlanSerializer
    queryset = TrafficSignPlan.objects.all()
    filterset_class = TrafficSignPlanFilterSet


class TrafficSignRealViewSet(TrafficControlViewSet):
    serializer_class = TrafficSignRealSerializer
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
