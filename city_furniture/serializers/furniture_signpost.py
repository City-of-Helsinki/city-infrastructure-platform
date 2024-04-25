from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models import (
    FurnitureSignpostPlan,
    FurnitureSignpostPlanFile,
    FurnitureSignpostReal,
    FurnitureSignpostRealFile,
    FurnitureSignpostRealOperation,
)
from city_furniture.models.common import CityFurnitureDeviceType
from traffic_control.models import OperationType
from traffic_control.serializers.common import EwktPointField, HideFromAnonUserSerializerMixin


class FurnitureSignpostPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FurnitureSignpostPlanFile
        fields = "__all__"


class FurnitureSignpostPlanSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = FurnitureSignpostPlanFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=CityFurnitureDeviceType.objects.for_target_model(CityFurnitureDeviceTypeTargetModel.FURNITURE_SIGNPOST)
    )
    target_name = serializers.CharField(read_only=True, source="target.name")
    device_type_description = serializers.CharField(read_only=True, source="device_type.description_fi")

    class Meta:
        model = FurnitureSignpostPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class FurnitureSignpostPlanGeoJSONSerializer(FurnitureSignpostPlanSerializer):
    location = GeometryField()


class FurnitureSignpostRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FurnitureSignpostRealFile
        fields = "__all__"


class FurnitureSignpostRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(furniture_signpost=True),
        source="operation_type",
    )

    class Meta:
        model = FurnitureSignpostRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        furniture_signpost_real = FurnitureSignpostReal.objects.get(
            pk=self.context["view"].kwargs["furniture_signpost_real_pk"]
        )
        validated_data["furniture_signpost_real"] = furniture_signpost_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        furniture_signpost_real = FurnitureSignpostReal.objects.get(
            pk=self.context["view"].kwargs["furniture_signpost_real_pk"]
        )
        validated_data["furniture_signpost_real"] = furniture_signpost_real
        return super().update(instance, validated_data)


class FurnitureSignpostRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = FurnitureSignpostRealFileSerializer(many=True, read_only=True)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=CityFurnitureDeviceType.objects.for_target_model(CityFurnitureDeviceTypeTargetModel.FURNITURE_SIGNPOST)
    )
    operations = FurnitureSignpostRealOperationSerializer(many=True, required=False, read_only=True)
    target_name = serializers.CharField(read_only=True, source="target.name_fi")
    device_type_description = serializers.CharField(read_only=True, source="device_type.description_fi")
    plan_decision_id = serializers.ReadOnlyField(source="furniture_signpost_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = FurnitureSignpostReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class FurnitureSignpostRealGeoJSONSerializer(FurnitureSignpostRealSerializer):
    location = GeometryField()
