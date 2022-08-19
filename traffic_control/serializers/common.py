from typing import Optional

from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_serializer_method
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import OperationalArea, Owner, TrafficControlDeviceType
from traffic_control.schema import TrafficSignType
from traffic_control.validators import validate_structured_content


class HideFromAnonUserSerializerMixin:
    """
    Don't include object's user information to unauthenticated requests
    """

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context["request"].user

        if not user.is_authenticated:
            representation.pop("created_by", None)
            representation.pop("updated_by", None)
            representation.pop("deleted_by", None)

        return representation


class StructuredContentValidator:
    """
    Validate structured content field against device type's content schema.
    Raises `ValidationError` if content is invalid.
    """

    requires_context = True

    def __call__(self, data, serializer):
        method = serializer.context["request"].method
        if method == "POST":
            content = data.get("content_s")
            device_type = data.get("device_type")

        elif method in ("PUT", "PATCH"):
            id = serializer.instance.id

            if "content_s" in data:
                content = data.get("content_s")
            else:
                content = serializer.Meta.model.objects.filter(id=id).first().content_s

            if "device_type" in data:
                device_type = data.get("device_type")
            else:
                device_type = serializer.Meta.model.objects.filter(id=id).first().device_type

        validation_errors = validate_structured_content(content, device_type)

        if validation_errors:
            raised_errors = []
            for e in validation_errors:
                raised_errors += e.messages
            raise serializers.ValidationError({"content_s": raised_errors})


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
