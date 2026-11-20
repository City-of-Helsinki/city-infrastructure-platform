from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from traffic_control.models import ResponsibleEntity
from traffic_control.serializers.common import NullToEmptyStringSerializerMixin


class ResponsibleEntitySerializer(
    EnumSupportSerializerMixin, NullToEmptyStringSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = ResponsibleEntity
        fields = [
            "id",
            "name",
            "organization_level",
            "parent",
        ]
