from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from .mixins import SoftDeleteMixin
from .models import TrafficSignPlan


class TrafficSignPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficSignPlan
        fields = ["id", "location_xy", "code", "decision_date", "lifecycle"]


class TrafficSignPlanViewSet(ModelViewSet, SoftDeleteMixin):
    serializer_class = TrafficSignPlanSerializer
    queryset = TrafficSignPlan.objects.all().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
