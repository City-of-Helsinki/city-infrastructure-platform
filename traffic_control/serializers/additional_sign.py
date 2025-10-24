from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignPlanFile,
    AdditionalSignReal,
    AdditionalSignRealFile,
    AdditionalSignRealOperation,
    OperationType,
    TrafficControlDeviceType,
)
from traffic_control.serializers.common import (
    EwktPointField,
    FileProxySerializerMixin,
    HideFromAnonUserSerializerMixin,
    PermissionFilteredRelatedField,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    StructuredContentValidator,
)
from traffic_control.services.additional_sign import additional_sign_plan_create, additional_sign_plan_update


class AdditionalSignPlanFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = AdditionalSignPlanFile
        fields = "__all__"


class AdditionalSignPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ADDITIONAL_SIGN),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return additional_sign_plan_create(validated_data)

    def update(self, instance, validated_data):
        return additional_sign_plan_update(instance, validated_data)

    class Meta:
        model = AdditionalSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")
        validators = (StructuredContentValidator(),)


class AdditionalSignPlanGeoJSONInputSerializer(AdditionalSignPlanInputSerializer):
    location = GeometryField(required=False)


class AdditionalSignPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ADDITIONAL_SIGN),
        allow_null=True,
        required=False,
    )
    files = PermissionFilteredRelatedField(
        permission_codename="traffic_control.view_additionalsignplanfile",
        serializer_class=AdditionalSignPlanFileSerializer,
    )

    class Meta:
        model = AdditionalSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class AdditionalSignPlanGeoJSONOutputSerializer(AdditionalSignPlanOutputSerializer):
    location = GeometryField(required=False)


class AdditionalSignRealFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = AdditionalSignRealFile
        fields = "__all__"


class AdditionalSignRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(additional_sign=True),
        source="operation_type",
    )

    class Meta:
        model = AdditionalSignRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        additional_sign_real = AdditionalSignReal.objects.get(pk=self.context["view"].kwargs["additional_sign_real_pk"])
        validated_data["additional_sign_real"] = additional_sign_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        additional_sign_real = AdditionalSignReal.objects.get(pk=self.context["view"].kwargs["additional_sign_real_pk"])
        validated_data["additional_sign_real"] = additional_sign_real
        return super().update(instance, validated_data)


class AdditionalSignRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ADDITIONAL_SIGN),
        allow_null=True,
        required=False,
    )
    operations = AdditionalSignRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="additional_sign_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = AdditionalSignReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "legacy_code", "is_active", "deleted_at", "deleted_by")
        validators = (StructuredContentValidator(),)


class AdditionalSignRealGeoJSONSerializer(AdditionalSignRealSerializer):
    location = GeometryField(required=False)
