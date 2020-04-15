from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.models import (
    BarrierPlan,
    BarrierPlanFile,
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostPlanFile,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightPlanFile,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
)
from traffic_control.models.mount import MountPlanFile
from traffic_control.models.road_marking import RoadMarkingPlanFile


class TrafficLightPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlanFile
        fields = "__all__"


class TrafficLightPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlanFile
        fields = ("file",)


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


class TrafficLightRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficLightReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficLightRealGeoJSONSerializer(TrafficLightRealSerializer):
    location = GeometryField()


class TrafficSignPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlanFile
        fields = "__all__"


class TrafficSignPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlanFile
        fields = ("file",)


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
    affect_area = GeometryField()


class TrafficSignRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficSignReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class TrafficSignRealGeoJSONSerializer(TrafficSignRealSerializer):
    location = GeometryField()
    affect_area = GeometryField()


class SignpostPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostPlanFile
        fields = "__all__"


class SignpostPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostPlanFile
        fields = ("file",)


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


class SignpostRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SignpostReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class SignpostRealGeoJSONSerializer(SignpostRealSerializer):
    location = GeometryField()


class MountPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountPlanFile
        fields = "__all__"


class MountPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountPlanFile
        fields = ("file",)


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


class MountRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    ordered_traffic_signs = serializers.PrimaryKeyRelatedField(
        read_only=True, many=True
    )

    class Meta:
        model = MountReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class MountRealGeoJSONSerializer(MountRealSerializer):
    location = GeometryField()


class BarrierPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPlanFile
        fields = "__all__"


class BarrierPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPlanFile
        fields = ("file",)


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


class BarrierRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = BarrierReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class BarrierRealGeoJSONSerializer(BarrierRealSerializer):
    location = GeometryField()


class RoadMarkingPlanFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingPlanFile
        fields = "__all__"


class RoadMarkingPlanPostFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingPlanFile
        fields = ("file",)


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


class RoadMarkingRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = RoadMarkingReal
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
        exclude = ("is_active", "deleted_at", "deleted_by")


class RoadMarkingRealGeoJSONSerializer(RoadMarkingRealSerializer):
    location = GeometryField()


class TrafficSignCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignCode
        fields = "__all__"


class PortalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalType
        fields = "__all__"
