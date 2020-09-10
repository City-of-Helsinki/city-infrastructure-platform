from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    BarrierRealFile,
    TrafficControlDeviceType,
)
from ..models.common import DeviceTypeTargetModel


class BarrierPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPlanFile
        fields = "__all__"


class BarrierPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = BarrierPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.BARRIER
        )
    )

    class Meta:
        model = BarrierPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class BarrierPlanGeoJSONSerializer(BarrierPlanSerializer):
    location = GeometryField()


class BarrierRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierRealFile
        fields = "__all__"


class BarrierRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = BarrierRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.BARRIER
        )
    )

    class Meta:
        model = BarrierReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class BarrierRealGeoJSONSerializer(BarrierRealSerializer):
    location = GeometryField()
