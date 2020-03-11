from enumfields.drf.serializers import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    PortalType,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)


class TrafficLightPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightPlan
        fields = ("plan_document",)


class TrafficLightPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficLightPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class TrafficLightPlanGeoJSONSerializer(TrafficLightPlanSerializer):
    location = GeometryField()


class TrafficLightRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficLightReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class TrafficSignPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlan
        fields = ("plan_document",)


class TrafficLightRealGeoJSONSerializer(TrafficLightRealSerializer):
    location = GeometryField()


class TrafficSignPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class TrafficSignPlanGeoJSONSerializer(TrafficSignPlanSerializer):
    location = GeometryField()
    affect_area = GeometryField()


class TrafficSignRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class SignpostPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignpostPlan
        fields = ("plan_document",)


class TrafficSignRealGeoJSONSerializer(TrafficSignRealSerializer):
    location = GeometryField()
    affect_area = GeometryField()


class SignpostPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SignpostPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class SignpostPlanGeoJSONSerializer(SignpostPlanSerializer):
    location = GeometryField()


class SignpostRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SignpostReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class MountPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountPlan
        fields = ("plan_document",)


class SignpostRealGeoJSONSerializer(SignpostRealSerializer):
    location = GeometryField()


class MountPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class MountPlanGeoJSONSerializer(MountPlanSerializer):
    location = GeometryField()


class MountRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = MountReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class BarrierPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPlan
        fields = ("plan_document",)


class MountRealGeoJSONSerializer(MountRealSerializer):
    location = GeometryField()


class BarrierPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = BarrierPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class BarrierPlanGeoJSONSerializer(BarrierPlanSerializer):
    location = GeometryField()


class BarrierRealSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = BarrierReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class RoadMarkingPlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadMarkingPlan
        fields = ("plan_document",)


class BarrierRealGeoJSONSerializer(BarrierRealSerializer):
    location = GeometryField()


class RoadMarkingPlanSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = RoadMarkingPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
            "plan_document",
        )


class RoadMarkingPlanGeoJSONSerializer(RoadMarkingPlanSerializer):
    location = GeometryField()


class RoadMarkingRealSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = RoadMarkingReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


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
