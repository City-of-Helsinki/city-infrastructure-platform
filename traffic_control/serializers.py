from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers

from traffic_control.models import (
    MountPlan,
    MountReal,
    TrafficSignPlan,
    TrafficSignReal,
)


class TrafficSignPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class TrafficSignRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class MountPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountPlan
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class MountRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
