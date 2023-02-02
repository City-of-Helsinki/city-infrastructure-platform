from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.models import (
    MountPlan,
    MountPlanFile,
    MountReal,
    MountRealFile,
    MountType,
    OperationType,
    PortalType,
)
from traffic_control.models.mount import MountRealOperation
from traffic_control.serializers.common import EwktGeometryField, HideFromAnonUserSerializerMixin


class PortalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalType
        fields = "__all__"


class MountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountType
        fields = "__all__"


class MountPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountPlanFile
        fields = "__all__"


class MountPlanSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    files = MountPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = MountPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class MountPlanGeoJSONSerializer(MountPlanSerializer):
    location = GeometryField()


class MountRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountRealFile
        fields = "__all__"


class MountRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(mount=True),
        source="operation_type",
    )

    class Meta:
        model = MountRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        mount_real = MountReal.objects.get(pk=self.context["view"].kwargs["mount_real_pk"])
        validated_data["mount_real"] = mount_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        mount_real = MountReal.objects.get(pk=self.context["view"].kwargs["mount_real_pk"])
        validated_data["mount_real"] = mount_real
        return super().update(instance, validated_data)


class MountRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    ordered_traffic_signs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    files = MountRealFileSerializer(many=True, read_only=True)
    operations = MountRealOperationSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = MountReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class MountRealGeoJSONSerializer(MountRealSerializer):
    location = GeometryField()
