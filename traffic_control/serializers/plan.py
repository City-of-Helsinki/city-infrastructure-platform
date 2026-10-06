from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.models import Plan
from traffic_control.serializers.common import EwktGeometryField, HideFromAnonUserSerializerMixin
from traffic_control.services.plan import get_plan_decision_url


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
    furniture_signpost_plan_ids = serializers.PrimaryKeyRelatedField(
        source="furniture_signpost_plans",
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
            "furniture_signpost_plan_ids",
        )


class PlanSerializer(HideFromAnonUserSerializerMixin, serializers.ModelSerializer):
    location = EwktGeometryField(required=False, allow_blank=True, allow_null=True)
    linked_objects = PlanRelationSerializer(source="*", required=False, read_only=True)

    class Meta:
        model = Plan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        fields = (
            "id",
            "location",
            "linked_objects",
            "created_at",
            "updated_at",
            "source_id",
            "source_name",
            "name",
            "decision_id",
            "diary_number",
            "drawing_numbers",
            "derive_location",
            "decision_date",
            "decision_url",
            "created_by",
            "updated_by",
        )

    def validate(self, attrs: dict) -> dict:
        """Populate `decision_url` from `diary_number` when no URL is available.

        An explicitly given `decision_url` is never overwritten. The URL is only
        derived when the resulting value would otherwise be empty.

        Args:
            attrs (dict): Validated field values.

        Returns:
            dict: Validated field values with `decision_url` populated when applicable.
        """
        attrs = super().validate(attrs)

        diary_number = attrs.get("diary_number", getattr(self.instance, "diary_number", None))
        decision_url = attrs.get("decision_url", getattr(self.instance, "decision_url", None))

        if not decision_url:
            attrs["decision_url"] = get_plan_decision_url(diary_number)

        return attrs


class PlanGeoJSONSerializer(PlanSerializer):
    location = GeometryField()
