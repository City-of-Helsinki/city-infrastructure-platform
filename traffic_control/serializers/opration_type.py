from rest_framework import serializers

from traffic_control.models import OperationType


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = "__all__"
