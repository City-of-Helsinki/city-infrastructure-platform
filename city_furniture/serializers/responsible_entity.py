from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from city_furniture.models.common import ResponsibleEntity


class ResponsibleEntitySerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = ResponsibleEntity
        fields = [
            "id",
            "name",
            "organization_level",
            "parent",
        ]
