from rest_framework import serializers
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from .models import TrafficSignPlan


class TrafficSignPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlan
        fields = ["id", "code", "location_xy", "decision_date"]


class TrafficSignPlanViewSet(ListModelMixin, GenericViewSet):
    queryset = TrafficSignPlan.objects.all().order_by("-created_at")
    serializer_class = TrafficSignPlanSerializer
