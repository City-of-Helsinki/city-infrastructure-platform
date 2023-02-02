from typing import Optional

from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema_field
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import OperationalArea, Owner, TrafficControlDeviceType
from traffic_control.schema import TrafficSignType
from traffic_control.validators import validate_structured_content


@extend_schema_field(
    {
        "type": "string",
        "format": "EWKT",
        "example": "SRID=3879;POINT Z (25496751.5 6673129.5 1.5)",
    }
)
class EwktPointField(serializers.CharField):
    pass


@extend_schema_field(
    {
        "type": "string",
        "format": "EWKT",
        "example": "SRID=3879;POLYGON Z (("
        + ", ".join(
            [
                "25497733.5 6672927.5 0",
                "25497946.5 6673032.5 0",
                "25498653.5 6673034.5 0",
                "25498987.5 6672708.5 0",
                "25498314.5 6672170.5 0",
                "25497651.5 6672629.5 0",
                "25497646.5 6672775.5 0",
                "25497733.5 6672927.5 0",
            ]
        )
        + "))",
    }
)
class EwktPolygonField(serializers.CharField):
    pass


@extend_schema_field(
    {
        "type": "string",
        "format": "EWKT",
        "example": "SRID=3879;MULTIPOLYGON Z ((("
        + ", ".join(
            [
                "25497733.5 6672927.5 0",
                "25497946.5 6673032.5 0",
                "25498653.5 6673034.5 0",
                "25498987.5 6672708.5 0",
                "25498314.5 6672170.5 0",
                "25497651.5 6672629.5 0",
                "25497646.5 6672775.5 0",
                "25497733.5 6672927.5 0",
            ]
        )
        + ")))",
    }
)
class EwktGeometryField(serializers.CharField):
    pass


# Don't include object's user information to unauthenticated requests
class HideFromAnonUserSerializerMixin:
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
        fields = "__all__"

    @extend_schema_field(field=TrafficSignType)
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
