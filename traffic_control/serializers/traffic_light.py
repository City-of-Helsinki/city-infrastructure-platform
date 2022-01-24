from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    OperationType,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
)
from traffic_control.models.traffic_light import TrafficLightRealOperation


class TrafficLightPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlanFile
        fields = "__all__"


class TrafficLightPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = TrafficLightPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_LIGHT)
    )

    class Meta:
        model = TrafficLightPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class TrafficLightPlanGeoJSONSerializer(TrafficLightPlanSerializer):
    location = GeometryField()


class TrafficLightRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightRealFile
        fields = "__all__"


class TrafficLightRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(traffic_light=True),
        source="operation_type",
    )

    class Meta:
        model = TrafficLightRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        traffic_light_real = TrafficLightReal.objects.get(pk=self.context["view"].kwargs["traffic_light_real_pk"])
        validated_data["traffic_light_real"] = traffic_light_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        traffic_light_real = TrafficLightReal.objects.get(pk=self.context["view"].kwargs["traffic_light_real_pk"])
        validated_data["traffic_light_real"] = traffic_light_real
        return super().update(instance, validated_data)


class TrafficLightRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = TrafficLightRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_LIGHT)
    )
    operations = TrafficLightRealOperationSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = TrafficLightReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class TrafficLightRealGeoJSONSerializer(TrafficLightRealSerializer):
    location = GeometryField()
