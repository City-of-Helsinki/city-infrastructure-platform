from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    OperationType,
    TrafficControlDeviceType,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from traffic_control.models.traffic_sign import TrafficSignRealOperation
from traffic_control.serializers.common import (
    EwktPointField,
    EwktPolygonField,
    FileProxySerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.traffic_sign import traffic_sign_plan_create, traffic_sign_plan_update


class TrafficSignPlanFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlanFile
        fields = "__all__"


class TrafficSignPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    affect_area = EwktPolygonField(required=False)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_SIGN),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return traffic_sign_plan_create(validated_data)

    def update(self, instance, validated_data):
        return traffic_sign_plan_update(instance, validated_data)

    class Meta:
        model = TrafficSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class TrafficSignPlanGeoJSONInputSerializer(TrafficSignPlanInputSerializer):
    location = GeometryField()


class TrafficSignPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    affect_area = EwktPolygonField(required=False)
    files = TrafficSignPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_SIGN),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = TrafficSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class TrafficSignPlanGeoJSONOutputSerializer(TrafficSignPlanInputSerializer):
    location = GeometryField()


class TrafficSignRealFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = TrafficSignRealFile
        fields = "__all__"


class TrafficSignRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(traffic_sign=True),
        source="operation_type",
    )

    class Meta:
        model = TrafficSignRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        traffic_sign_real = TrafficSignReal.objects.get(pk=self.context["view"].kwargs["traffic_sign_real_pk"])
        validated_data["traffic_sign_real"] = traffic_sign_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        traffic_sign_real = TrafficSignReal.objects.get(pk=self.context["view"].kwargs["traffic_sign_real_pk"])
        validated_data["traffic_sign_real"] = traffic_sign_real
        return super().update(instance, validated_data)


class TrafficSignRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = TrafficSignRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_SIGN),
        allow_null=True,
        required=False,
    )
    operations = TrafficSignRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="traffic_sign_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = TrafficSignReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "legacy_code", "is_active", "deleted_at", "deleted_by")


class TrafficSignRealGeoJSONSerializer(TrafficSignRealSerializer):
    location = GeometryField()
