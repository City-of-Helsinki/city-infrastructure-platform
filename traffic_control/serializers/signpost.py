from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    OperationType,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    SignpostRealFile,
    TrafficControlDeviceType,
)
from traffic_control.models.signpost import SignpostRealOperation
from traffic_control.serializers.common import (
    EwktPointField,
    FileProxySerializerMixin,
    HideFromAnonUserSerializerMixin,
    PermissionFilteredRelatedField,
    ReplaceableDeviceInputSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
)
from traffic_control.services.signpost import signpost_plan_create, signpost_plan_update


class SignpostPlanFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SignpostPlanFile
        fields = "__all__"


class SignpostPlanInputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceInputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.SIGNPOST),
        allow_null=True,
        required=False,
    )

    def create(self, validated_data):
        return signpost_plan_create(validated_data)

    def update(self, instance, validated_data):
        return signpost_plan_update(instance, validated_data)

    class Meta:
        model = SignpostPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class SignpostPlanGeoJSONInputSerializer(SignpostPlanInputSerializer):
    location = GeometryField()


class SignpostPlanOutputSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    ReplaceableDeviceOutputSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = PermissionFilteredRelatedField(
        permission_codename="traffic_control.view_signpostplanfile",
        serializer_class=SignpostPlanFileSerializer,
    )
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.SIGNPOST),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = SignpostPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class SignpostPlanGeoJSONOutputSerializer(SignpostPlanOutputSerializer):
    location = GeometryField()


class SignpostRealFileSerializer(FileProxySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SignpostRealFile
        fields = "__all__"


class SignpostRealOperationSerializer(serializers.ModelSerializer):
    operation_type = serializers.StringRelatedField()
    operation_type_id = serializers.PrimaryKeyRelatedField(
        queryset=OperationType.objects.filter(signpost=True),
        source="operation_type",
    )

    class Meta:
        model = SignpostRealOperation
        fields = ("id", "operation_type", "operation_type_id", "operation_date")

    def create(self, validated_data):
        # Inject related object to validated data
        signpost_real = SignpostReal.objects.get(pk=self.context["view"].kwargs["signpost_real_pk"])
        validated_data["signpost_real"] = signpost_real
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Inject related object to validated data
        signpost_real = SignpostReal.objects.get(pk=self.context["view"].kwargs["signpost_real_pk"])
        validated_data["signpost_real"] = signpost_real
        return super().update(instance, validated_data)


class SignpostRealSerializer(
    EnumSupportSerializerMixin,
    HideFromAnonUserSerializerMixin,
    serializers.ModelSerializer,
):
    location = EwktPointField()
    files = PermissionFilteredRelatedField(
        permission_codename="traffic_control.view_signpostrealfile",
        serializer_class=SignpostRealFileSerializer,
    )
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.SIGNPOST),
        allow_null=True,
        required=False,
    )
    operations = SignpostRealOperationSerializer(many=True, required=False, read_only=True)
    plan_decision_id = serializers.ReadOnlyField(source="signpost_plan.plan.decision_id", allow_null=True)

    class Meta:
        model = SignpostReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class SignpostRealGeoJSONSerializer(SignpostRealSerializer):
    location = GeometryField()
