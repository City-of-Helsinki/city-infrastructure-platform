from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from city_furniture.models.common import CityFurnitureColor


class CityFurnitureColorSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CityFurnitureColor
        fields = "__all__"
