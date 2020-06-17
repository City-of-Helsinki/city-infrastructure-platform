from typing import Optional

from django.core.exceptions import ValidationError
from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from .models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    BarrierRealFile,
    MountPlan,
    MountPlanFile,
    MountReal,
    MountRealFile,
    MountType,
    Plan,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingPlanFile,
    RoadMarkingReal,
    RoadMarkingRealFile,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    SignpostRealFile,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficLightRealFile,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from .models.common import DeviceTypeTargetModel


class TrafficLightPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlanFile
        fields = "__all__"


class TrafficLightPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = TrafficLightPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = TrafficLightPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficLightPlanGeoJSONSerializer(TrafficLightPlanSerializer):
    location = GeometryField()


class TrafficLightRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightRealFile
        fields = "__all__"


class TrafficLightRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = TrafficLightRealFileSerializer(many=True, read_only=True)

    class Meta:
        model = TrafficLightReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficLightRealGeoJSONSerializer(TrafficLightRealSerializer):
    location = GeometryField()


class TrafficSignPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlanFile
        fields = "__all__"


class TrafficSignPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = TrafficSignPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = TrafficSignPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficSignPlanGeoJSONSerializer(TrafficSignPlanSerializer):
    location = GeometryField()
    affect_area = GeometryField(required=False)


class TrafficSignRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignRealFile
        fields = "__all__"


class TrafficSignRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = TrafficSignRealFileSerializer(many=True, read_only=True)

    class Meta:
        model = TrafficSignReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficSignRealGeoJSONSerializer(TrafficSignRealSerializer):
    location = GeometryField()
    affect_area = GeometryField(required=False)


class SignpostPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostPlanFile
        fields = "__all__"


class SignpostPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = SignpostPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = SignpostPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class SignpostPlanGeoJSONSerializer(SignpostPlanSerializer):
    location = GeometryField()


class SignpostRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostRealFile
        fields = "__all__"


class SignpostRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = SignpostRealFileSerializer(many=True, read_only=True)

    class Meta:
        model = SignpostReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class SignpostRealGeoJSONSerializer(SignpostRealSerializer):
    location = GeometryField()


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


class MountRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    ordered_traffic_signs = serializers.PrimaryKeyRelatedField(
        read_only=True, many=True
    )
    files = MountRealFileSerializer(many=True, read_only=True)

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


class BarrierPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPlanFile
        fields = "__all__"


class BarrierPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = BarrierPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = BarrierPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class BarrierPlanGeoJSONSerializer(BarrierPlanSerializer):
    location = GeometryField()


class BarrierRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierRealFile
        fields = "__all__"


class BarrierRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    files = BarrierRealFileSerializer(many=True, read_only=True)

    class Meta:
        model = BarrierReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class BarrierRealGeoJSONSerializer(BarrierRealSerializer):
    location = GeometryField()


class RoadMarkingPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingPlanFile
        fields = "__all__"


class RoadMarkingPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = RoadMarkingPlanFileSerializer(many=True, read_only=True)

    class Meta:
        model = RoadMarkingPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class RoadMarkingPlanGeoJSONSerializer(RoadMarkingPlanSerializer):
    location = GeometryField()


class RoadMarkingRealFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingRealFile
        fields = "__all__"


class RoadMarkingRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    files = RoadMarkingRealFileSerializer(many=True, read_only=True)

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


class PlanRelationSerializer(serializers.ModelSerializer):
    barrier = serializers.PrimaryKeyRelatedField(
        source="barrier_plans", many=True, queryset=BarrierPlan.objects.active()
    )
    mount = serializers.PrimaryKeyRelatedField(
        source="mount_plans", many=True, queryset=MountPlan.objects.active()
    )
    road_marking = serializers.PrimaryKeyRelatedField(
        source="road_marking_plans",
        many=True,
        queryset=RoadMarkingPlan.objects.active(),
    )
    signpost = serializers.PrimaryKeyRelatedField(
        source="signpost_plans", many=True, queryset=SignpostPlan.objects.active()
    )
    traffic_light = serializers.PrimaryKeyRelatedField(
        source="traffic_light_plans",
        many=True,
        queryset=TrafficLightPlan.objects.active(),
    )
    traffic_sign = serializers.PrimaryKeyRelatedField(
        source="traffic_sign_plans",
        many=True,
        queryset=TrafficSignPlan.objects.active(),
    )

    class Meta:
        model = Plan
        fields = (
            "barrier",
            "mount",
            "road_marking",
            "signpost",
            "traffic_light",
            "traffic_sign",
        )


class PlanSerializer(serializers.ModelSerializer):
    plans = PlanRelationSerializer(source="*")

    class Meta:
        model = Plan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("is_active", "deleted_at", "deleted_by")


class PlanGeoJSONSerializer(PlanSerializer):
    location = GeometryField()


class TrafficControlDeviceTypeSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficControlDeviceType
        fields = "__all__"

    def validate_target_model(
        self, value: Optional[DeviceTypeTargetModel]
    ) -> Optional[DeviceTypeTargetModel]:
        try:
            self.instance.validate_change_target_model(value, raise_exception=True)
        except ValidationError as error:
            raise serializers.ValidationError(error.message)

        return value


class PortalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalType
        fields = "__all__"


class MountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountType
        fields = "__all__"
