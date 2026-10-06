from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
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
from traffic_control.serializers.common import (
    EwktGeometryField,
    FileProxySerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.mount import mount_plan_create, mount_plan_update


class PortalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalType
        fields = (
            "id",
            "structure",
            "build_type",
            "model",
        )


class MountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountType
        fields = (
            "id",
            "code",
            "description",
            "description_fi",
            "description_sv",
            "digiroad_code",
            "digiroad_description",
        )


class MountPlanFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountPlanFile
        fields = (
            "id",
            "is_public",
            "file",
            "mount_plan",
        )


class MountPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()

    def create(self, validated_data):
        return mount_plan_create(validated_data)

    def update(self, instance, validated_data):
        return mount_plan_update(instance, validated_data)

    class Meta:
        model = MountPlan
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
            "created_at",
            "updated_at",
            "lifecycle",
            "source_id",
            "source_name",
            "height",
            "base",
            "material",
            "txt",
            "electric_accountable",
            "is_foldable",
            "cross_bar_length",
            "road_name",
            "location_specifier",
            "created_by",
            "updated_by",
            "owner",
            "mount_type",
            "portal_type",
            "plan",
        )


class MountPlanGeoJSONInputSerializer(MountPlanInputSerializer):
    location = GeometryField()


class MountPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
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
        fields = (
            "id",
            "replaces",
            "replaced_by",
            "is_replaced",
            "location",
            "files",
            "created_at",
            "updated_at",
            "lifecycle",
            "source_id",
            "source_name",
            "height",
            "base",
            "material",
            "txt",
            "electric_accountable",
            "is_foldable",
            "cross_bar_length",
            "road_name",
            "location_specifier",
            "created_by",
            "updated_by",
            "owner",
            "mount_type",
            "portal_type",
            "plan",
        )


class MountPlanGeoJSONOutputSerializer(MountPlanOutputSerializer):
    location = GeometryField()


class MountRealFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountRealFile
        fields = (
            "id",
            "is_public",
            "file",
            "mount_real",
        )


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


@extend_schema_field(OpenApiTypes.UUID)
class OrderedTrafficSignsField(serializers.PrimaryKeyRelatedField):
    pass


class MountRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktGeometryField()
    ordered_traffic_signs = OrderedTrafficSignsField(read_only=True, many=True)
    files = MountRealFileSerializer(many=True, read_only=True)
    operations = MountRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="mount_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = MountReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        fields = (
            "id",
            "location",
            "ordered_traffic_signs",
            "files",
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
            "height",
            "base",
            "material",
            "txt",
            "electric_accountable",
            "is_foldable",
            "cross_bar_length",
            "road_name",
            "location_specifier",
            "inspected_at",
            "diameter",
            "scanned_at",
            "attachment_url",
            "created_by",
            "updated_by",
            "owner",
            "mount_type",
            "portal_type",
            "mount_plan",
        )


class MountRealGeoJSONSerializer(MountRealSerializer):
    location = GeometryField()
