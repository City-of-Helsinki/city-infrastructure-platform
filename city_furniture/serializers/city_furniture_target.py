from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from city_furniture.models.common import CityFurnitureTarget


class CityFurnitureTargetSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CityFurnitureTarget
        fields = "__all__"
