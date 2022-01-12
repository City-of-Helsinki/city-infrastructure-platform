from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import MountPlan, MountPlanFile, MountReal, MountRealFile, MountType, PortalType
from ..models.mount import MountRealOperation


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


class MountPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
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

    class Meta:
        model = MountRealOperation
        fields = ("id", "operation_type", "operation_date")


class MountRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
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
