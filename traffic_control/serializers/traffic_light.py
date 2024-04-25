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
from traffic_control.serializers.common import (
    EwktPointField,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.traffic_light import traffic_light_plan_create, traffic_light_plan_update


class TrafficLightPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlanFile
        fields = "__all__"


class TrafficLightPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_LIGHT),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return traffic_light_plan_create(validated_data)

    def update(self, instance, validated_data):
        return traffic_light_plan_update(instance, validated_data)

    class Meta:
        model = TrafficLightPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class TrafficLightPlanGeoJSONInputSerializer(TrafficLightPlanInputSerializer):
    location = GeometryField()


class TrafficLightPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = TrafficLightPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_LIGHT),
        allow_null=True,
        required=False,
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


class TrafficLightPlanGeoJSONOutputSerializer(TrafficLightPlanOutputSerializer):
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


class TrafficLightRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = TrafficLightRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_LIGHT),
        allow_null=True,
        required=False,
    )
    operations = TrafficLightRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="traffic_light_plan.plan.decision_id", allow_null=True)

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
