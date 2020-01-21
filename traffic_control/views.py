from rest_framework.viewsets import ModelViewSet

from traffic_control.mixins import SoftDeleteMixin, UserCreateMixin, UserUpdateMixin
from traffic_control.models import (
    MountPlan,
    MountReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.serializers import (
    MountPlanSerializer,
    MountRealSerializer,
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


class MountPlanViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    serializer_class = MountPlanSerializer
    queryset = MountPlan.objects.all().order_by("-created_at")


class MountRealViewSet(ModelViewSet, UserCreateMixin, UserUpdateMixin, SoftDeleteMixin):
    serializer_class = MountRealSerializer
    queryset = MountReal.objects.all().order_by("-created_at")
