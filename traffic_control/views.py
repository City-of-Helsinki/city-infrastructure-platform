from rest_framework.viewsets import ModelViewSet

from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    BarrierPlan,
    MountPlan,
    MountReal,
    SignpostPlan,
    SignpostReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.serializers import (
    BarrierPlanSerializer,
    MountPlanSerializer,
    MountRealSerializer,
    SignpostPlanSerializer,
    SignpostRealSerializer,
    TrafficSignPlanSerializer,
    TrafficSignRealSerializer,
)


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
