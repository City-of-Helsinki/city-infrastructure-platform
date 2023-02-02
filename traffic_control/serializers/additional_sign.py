from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, OperationType
from traffic_control.models.additional_sign import AdditionalSignRealOperation
from traffic_control.serializers.common import (
    EwktPointField,
    HideFromAnonUserSerializerMixin,
    StructuredContentValidator,
)


class AdditionalSignPlanSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()

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


class AdditionalSignPlanGeoJSONSerializer(AdditionalSignPlanSerializer):
    location = GeometryField(required=False)


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
    operations = AdditionalSignRealOperationSerializer(many=True, required=False, read_only=True)

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
