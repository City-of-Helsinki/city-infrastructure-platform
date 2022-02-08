from typing import Optional

from django.core.exceptions import ValidationError
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models.common import CityFurnitureDeviceType


class CityFurnitureDeviceTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = CityFurnitureDeviceType
        fields = "__all__"

    def validate_target_model(
        self, value: Optional[CityFurnitureDeviceTypeTargetModel]
    ) -> Optional[CityFurnitureDeviceTypeTargetModel]:
        if self.instance and self.instance.target_model != value:
            try:
                self.instance.validate_change_target_model(value, raise_exception=True)
            except ValidationError as error:
                raise serializers.ValidationError(error.message)

        return value
