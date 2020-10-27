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
    barrier_plan_ids = serializers.PrimaryKeyRelatedField(
        source="barrier_plans",
        many=True,
        queryset=BarrierPlan.objects.active(),
        required=False,
    )
    mount_plan_ids = serializers.PrimaryKeyRelatedField(
        source="mount_plans",
        many=True,
        queryset=MountPlan.objects.active(),
        required=False,
    )
    road_marking_plan_ids = serializers.PrimaryKeyRelatedField(
        source="road_marking_plans",
        many=True,
        queryset=RoadMarkingPlan.objects.active(),
        required=False,
    )
    signpost_plan_ids = serializers.PrimaryKeyRelatedField(
        source="signpost_plans",
        many=True,
        queryset=SignpostPlan.objects.active(),
        required=False,
    )
    traffic_light_plan_ids = serializers.PrimaryKeyRelatedField(
        source="traffic_light_plans",
        many=True,
        queryset=TrafficLightPlan.objects.active(),
        required=False,
    )
    traffic_sign_plan_ids = serializers.PrimaryKeyRelatedField(
        source="traffic_sign_plans",
        many=True,
        queryset=TrafficSignPlan.objects.active(),
        required=False,
    )
    additional_sign_plan_ids = serializers.PrimaryKeyRelatedField(
        source="additional_sign_plans",
        many=True,
        queryset=AdditionalSignPlan.objects.all(),
        required=False,
    )

    class Meta:
        model = Plan
        fields = (
            "barrier_plan_ids",
            "mount_plan_ids",
            "road_marking_plan_ids",
            "signpost_plan_ids",
            "traffic_light_plan_ids",
            "traffic_sign_plan_ids",
            "additional_sign_plan_ids",
        )


class PlanSerializer(serializers.ModelSerializer):
    linked_objects = PlanRelationSerializer(source="*", required=False)

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
