from rest_framework.viewsets import ModelViewSet

from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.serializers import (
    BarrierPlanSerializer,
    BarrierRealSerializer,
    MountPlanSerializer,
    MountRealSerializer,
    RoadMarkingPlanSerializer,
    RoadMarkingRealSerializer,
    SignpostPlanSerializer,
    SignpostRealSerializer,
    TrafficLightPlanSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealSerializer,
)


class TrafficLightPlanViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = TrafficLightPlanSerializer
    queryset = TrafficLightPlan.objects.all().order_by("-created_at")


class TrafficSignPlanViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = TrafficSignPlanSerializer
    queryset = TrafficSignPlan.objects.all().order_by("-created_at")


class TrafficSignRealViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = TrafficSignRealSerializer
    queryset = TrafficSignReal.objects.all().order_by("-created_at")


class SignpostPlanViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = SignpostPlanSerializer
    queryset = SignpostPlan.objects.all().order_by("-created_at")


class SignpostRealViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = SignpostRealSerializer
    queryset = SignpostReal.objects.all().order_by("-created_at")


class MountPlanViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    serializer_class = MountPlanSerializer
    queryset = MountPlan.objects.all().order_by("-created_at")


class MountRealViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.all().order_by("-created_at")


class BarrierPlanViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = BarrierPlanSerializer
    queryset = BarrierPlan.objects.all().order_by("-created_at")


class BarrierRealViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = BarrierRealSerializer
    queryset = BarrierReal.objects.all().order_by("-created_at")


class RoadMarkingPlanViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = RoadMarkingPlanSerializer
    queryset = RoadMarkingPlan.objects.all().order_by("-created_at")


class RoadMarkingRealViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    serializer_class = RoadMarkingRealSerializer
    queryset = RoadMarkingReal.objects.all().order_by("-created_at")
