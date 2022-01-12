from typing import Optional

from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_serializer_method
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import OperationalArea, Owner, TrafficControlDeviceType
from ..models.common import DeviceTypeTargetModel
from ..schema import TrafficSignType


class TrafficControlDeviceTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    traffic_sign_type = serializers.SerializerMethodField(
        method_name="get_traffic_sign_type",
    )

    class Meta:
        model = TrafficControlDeviceType
        exclude = ("legacy_code", "legacy_description")

    @swagger_serializer_method(serializer_or_field=TrafficSignType)
    def get_traffic_sign_type(self, obj):
        value = obj.traffic_sign_type
        if value:
            return {"code": obj.code[0], "type": value}
        return None

    def validate_target_model(self, value: Optional[DeviceTypeTargetModel]) -> Optional[DeviceTypeTargetModel]:
        if self.instance and self.instance.target_model != value:
            try:
                self.instance.validate_change_target_model(value, raise_exception=True)
            except ValidationError as error:
                raise serializers.ValidationError(error.message)

        return value


class OperationalAreaSerializer(serializers.ModelSerializer):
    location = GeometryField()

    class Meta:
        model = OperationalArea
        fields = "__all__"


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = "__all__"
