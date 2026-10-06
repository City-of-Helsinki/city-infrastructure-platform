from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    BarrierRealFile,
    OperationType,
    TrafficControlDeviceType,
)
from traffic_control.models.barrier import BarrierRealOperation
from traffic_control.serializers.common import (
    EwktGeometryField,
    FileProxySerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.barrier import barrier_plan_create, barrier_plan_update


class BarrierPlanFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = BarrierPlanFile
        fields = (
            "id",
            "is_public",
            "file",
            "barrier_plan",
        )


class BarrierPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.BARRIER),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return barrier_plan_create(validated_data)

    def update(self, instance, validated_data):
        return barrier_plan_update(instance, validated_data)

    class Meta:
        model = BarrierPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        fields = (
            "id",
            "replaces",
            "location",
            "device_type",
            "created_at",
            "updated_at",
            "lifecycle",
            "source_id",
            "source_name",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "connection_type",
            "material",
            "is_electric",
            "reflective",
            "validity_period_start",
            "validity_period_end",
            "length",
            "count",
            "txt",
            "created_by",
            "updated_by",
            "owner",
            "plan",
        )


class BarrierPlanGeoJSONInputSerializer(BarrierPlanInputSerializer):
    location = GeometryField()


class BarrierPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    files = BarrierPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.BARRIER),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = BarrierPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        fields = (
            "id",
            "replaces",
            "replaced_by",
            "is_replaced",
            "location",
            "files",
            "device_type",
            "created_at",
            "updated_at",
            "lifecycle",
            "source_id",
            "source_name",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "connection_type",
            "material",
            "is_electric",
            "reflective",
            "validity_period_start",
            "validity_period_end",
            "length",
            "count",
            "txt",
            "created_by",
            "updated_by",
            "owner",
            "plan",
        )


class BarrierPlanGeoJSONOutputSerializer(BarrierPlanOutputSerializer):
    location = GeometryField()


class BarrierRealFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = BarrierRealFile
        fields = (
            "id",
            "is_public",
            "file",
            "barrier_real",
        )


class BarrierRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(barrier=True),
        source="operation_type",
    )

    class Meta:
        model = BarrierRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        barrier_real = BarrierReal.objects.get(pk=self.context["view"].kwargs["barrier_real_pk"])
        validated_data["barrier_real"] = barrier_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        barrier_real = BarrierReal.objects.get(pk=self.context["view"].kwargs["barrier_real_pk"])
        validated_data["barrier_real"] = barrier_real
        return super().update(instance, validated_data)


class BarrierRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    files = BarrierRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.BARRIER),
        allow_null=True,
        required=False,
    )
    operations = BarrierRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="barrier_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = BarrierReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        fields = (
            "id",
            "location",
            "files",
            "device_type",
            "operations",
            "plan_decision_id",
            "created_at",
            "updated_at",
            "lifecycle",
            "installation_date",
            "installation_status",
            "condition",
            "source_id",
            "source_name",
            "road_name",
            "lane_number",
            "lane_type",
            "location_specifier",
            "connection_type",
            "material",
            "is_electric",
            "reflective",
            "validity_period_start",
            "validity_period_end",
            "length",
            "count",
            "txt",
            "created_by",
            "updated_by",
            "owner",
            "barrier_plan",
        )


class BarrierRealGeoJSONSerializer(BarrierRealSerializer):
    location = GeometryField()
