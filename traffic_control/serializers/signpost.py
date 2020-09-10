from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import (
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    SignpostRealFile,
    TrafficControlDeviceType,
)
from ..models.common import DeviceTypeTargetModel


class SignpostPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostPlanFile
        fields = "__all__"


class SignpostPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = SignpostPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.SIGNPOST
        )
    )

    class Meta:
        model = SignpostPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class SignpostPlanGeoJSONSerializer(SignpostPlanSerializer):
    location = GeometryField()


class SignpostRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostRealFile
        fields = "__all__"


class SignpostRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = SignpostRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.SIGNPOST
        )
    )

    class Meta:
        model = SignpostReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class SignpostRealGeoJSONSerializer(SignpostRealSerializer):
    location = GeometryField()
