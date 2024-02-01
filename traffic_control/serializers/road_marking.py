from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    OperationType,
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
    TrafficControlDeviceType,
)
from traffic_control.models.road_marking import RoadMarkingRealOperation
from traffic_control.serializers.common import (
    EwktGeometryField,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.road_marking import road_marking_plan_create, road_marking_plan_update


class RoadMarkingPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingPlanFile
        fields = "__all__"


class RoadMarkingPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ROAD_MARKING),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return road_marking_plan_create(validated_data)

    def update(self, instance, validated_data):
        return road_marking_plan_update(instance, validated_data)

    class Meta:
        model = RoadMarkingPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class RoadMarkingPlanGeoJSONInputSerializer(RoadMarkingPlanInputSerializer):
    location = GeometryField()


class RoadMarkingPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    files = RoadMarkingPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ROAD_MARKING),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = RoadMarkingPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class RoadMarkingPlanGeoJSONOutputSerializer(RoadMarkingPlanOutputSerializer):
    location = GeometryField()


class RoadMarkingRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingRealFile
        fields = "__all__"


class RoadMarkingRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(road_marking=True),
        source="operation_type",
    )

    class Meta:
        model = RoadMarkingRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        road_marking_real = RoadMarkingReal.objects.get(pk=self.context["view"].kwargs["road_marking_real_pk"])
        validated_data["road_marking_real"] = road_marking_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        road_marking_real = RoadMarkingReal.objects.get(pk=self.context["view"].kwargs["road_marking_real_pk"])
        validated_data["road_marking_real"] = road_marking_real
        return super().update(instance, validated_data)


class RoadMarkingRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    files = RoadMarkingRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ROAD_MARKING),
        allow_null=True,
        required=False,
    )
    operations = RoadMarkingRealOperationSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = RoadMarkingReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class RoadMarkingRealGeoJSONSerializer(RoadMarkingRealSerializer):
    location = GeometryField()
