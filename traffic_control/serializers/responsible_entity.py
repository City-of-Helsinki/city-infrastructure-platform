from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from traffic_control.models import ResponsibleEntity


class ResponsibleEntitySerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ResponsibleEntity
        fields = [
            "id",
            "name",
            "organization_level",
            "parent",
        ]
