from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import Plan


class PlanRelationSerializer(serializers.ModelSerializer):
    barrier_plan_ids = serializers.PrimaryKeyRelatedField(
        source="barrier_plans",
        many=True,
        required=False,
        read_only=True,
    )
    mount_plan_ids = serializers.PrimaryKeyRelatedField(
        source="mount_plans",
        many=True,
        required=False,
        read_only=True,
    )
    road_marking_plan_ids = serializers.PrimaryKeyRelatedField(
        source="road_marking_plans",
        many=True,
        required=False,
        read_only=True,
    )
    signpost_plan_ids = serializers.PrimaryKeyRelatedField(
        source="signpost_plans",
        many=True,
        required=False,
        read_only=True,
    )
    traffic_light_plan_ids = serializers.PrimaryKeyRelatedField(
        source="traffic_light_plans",
        many=True,
        required=False,
        read_only=True,
    )
    traffic_sign_plan_ids = serializers.PrimaryKeyRelatedField(
        source="traffic_sign_plans",
        many=True,
        required=False,
        read_only=True,
    )
    additional_sign_plan_ids = serializers.PrimaryKeyRelatedField(
        source="additional_sign_plans",
        many=True,
        required=False,
        read_only=True,
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
    linked_objects = PlanRelationSerializer(source="*", required=False, read_only=True)

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
