from rest_framework import serializers

from traffic_control.models import OperationType


class OperationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationType
        fields = (
            "id",
            "name",
            "traffic_sign",
            "additional_sign",
            "road_marking",
            "barrier",
            "signpost",
            "traffic_light",
            "furniture_signpost",
            "mount",
        )
