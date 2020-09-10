from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import (
    AdditionalSignPlan,
    BarrierPlan,
    MountPlan,
    Plan,
    RoadMarkingPlan,
    SignpostPlan,
    TrafficLightPlan,
    TrafficSignPlan,
)


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
    additional_sign = serializers.PrimaryKeyRelatedField(
        source="additional_sign_plans",
        many=True,
        queryset=AdditionalSignPlan.objects.all(),
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
            "additional_sign",
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
