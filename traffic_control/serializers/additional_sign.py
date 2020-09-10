from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
    TrafficControlDeviceType,
)
from ..models.common import DeviceTypeTargetModel


class AdditionalSignContentPlanSerializer(serializers.ModelSerializer):
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
        )


class AdditionalSignContentRealSerializer(serializers.ModelSerializer):
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentReal
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
        )


class AdditionalSignPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    content = AdditionalSignContentPlanSerializer(many=True, read_only=True)

    class Meta:
        model = AdditionalSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class AdditionalSignPlanGeoJSONSerializer(AdditionalSignPlanSerializer):
    location = GeometryField(required=False)
    affect_area = GeometryField(required=False)


class AdditionalSignRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    content = AdditionalSignContentRealSerializer(many=True, read_only=True)

    class Meta:
        model = AdditionalSignReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "legacy_code", "is_active", "deleted_at", "deleted_by")


class AdditionalSignRealGeoJSONSerializer(AdditionalSignRealSerializer):
    location = GeometryField(required=False)
    affect_area = GeometryField(required=False)
