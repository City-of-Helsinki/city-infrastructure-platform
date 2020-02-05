from rest_framework.filters import OrderingFilter
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
    TrafficLightReal,
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
    TrafficLightRealSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealSerializer,
)


class TrafficControlViewSet(
    ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin
):
    filter_backends = [OrderingFilter]
    ordering_fields = "__all__"
    ordering = ["-created_at"]


class TrafficLightPlanViewSet(TrafficControlViewSet):
    serializer_class = TrafficLightPlanSerializer
    queryset = TrafficLightPlan.objects.all()


class TrafficLightRealViewSet(TrafficControlViewSet):
    serializer_class = TrafficLightRealSerializer
    queryset = TrafficLightReal.objects.all()


class TrafficSignPlanViewSet(TrafficControlViewSet):
    serializer_class = TrafficSignPlanSerializer
    queryset = TrafficSignPlan.objects.all()


class TrafficSignRealViewSet(TrafficControlViewSet):
    serializer_class = TrafficSignRealSerializer
    queryset = TrafficSignReal.objects.all()


class SignpostPlanViewSet(TrafficControlViewSet):
    serializer_class = SignpostPlanSerializer
    queryset = SignpostPlan.objects.all()


class SignpostRealViewSet(TrafficControlViewSet):
    serializer_class = SignpostRealSerializer
    queryset = SignpostReal.objects.all()


class MountPlanViewSet(TrafficControlViewSet):
    serializer_class = MountPlanSerializer
    queryset = MountPlan.objects.all()


class MountRealViewSet(TrafficControlViewSet):
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.all()


class BarrierPlanViewSet(TrafficControlViewSet):
    serializer_class = BarrierPlanSerializer
    queryset = BarrierPlan.objects.all()


class BarrierRealViewSet(TrafficControlViewSet):
    serializer_class = BarrierRealSerializer
    queryset = BarrierReal.objects.all()


class RoadMarkingPlanViewSet(TrafficControlViewSet):
    serializer_class = RoadMarkingPlanSerializer
    queryset = RoadMarkingPlan.objects.all()


class RoadMarkingRealViewSet(TrafficControlViewSet):
    serializer_class = RoadMarkingRealSerializer
    queryset = RoadMarkingReal.objects.all()
