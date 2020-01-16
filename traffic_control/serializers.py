from rest_framework import serializers

from traffic_control.models import TrafficSignPlan, TrafficSignReal


class TrafficSignPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlan
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")


class TrafficSignRealSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignReal
        fields = "__all__"
        read_only_fields = ("created_by", "updated_by", "deleted_by", "deleted_at")
