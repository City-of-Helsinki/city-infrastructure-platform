from rest_framework import serializers

from traffic_control.models import TrafficSignPlan, TrafficSignReal


class TrafficSignPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlan
        fields = ["id", "location_xy", "code", "decision_date", "lifecycle"]


class TrafficSignRealSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignReal
        fields = ["id", "location_xy", "code", "installation_date", "lifecycle"]
