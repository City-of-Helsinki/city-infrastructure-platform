from typing import Optional, OrderedDict
from uuid import UUID

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import OperationalArea, Owner, TrafficControlDeviceType
from traffic_control.schema import IconsType, TrafficSignType
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


class FileProxySerializerMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if "file" in representation:
            request = self.context.get("request")
            representation["file"] = f"{request.scheme}://{request.get_host()}/uploads/{instance.file.name}"
        return representation


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


class AdditionalSignParentValidationMixin:
    """
    Mixin that validates parent field is provided for non-ticket-machine additional signs.

    This mixin should be used with AdditionalSign serializers to enforce the business rule
    that only ticket machine device types can have a null parent.
    """

    def _is_update(self) -> bool:
        """Check whether the current serializer operation is an update.

        Returns:
            bool: True if the serializer has an existing instance (update), False otherwise.
        """
        return hasattr(self, "instance") and self.instance is not None

    def _resolve_effective_parents(self, data: dict, is_update: bool) -> tuple:
        """Resolve the effective parent, signpost_plan, and signpost_real values.

        For updates, falls back to existing instance values when not explicitly provided.

        Args:
            data (dict): The validated data dictionary.
            is_update (bool): Whether the current operation is an update.

        Returns:
            tuple: A tuple of (parent, signpost_plan, signpost_real).
        """
        parent = data.get("parent") if not is_update or "parent" in data else self.instance.parent
        signpost_plan = (
            data.get("signpost_plan")
            if not is_update or "signpost_plan" in data
            else getattr(self.instance, "signpost_plan", None)
        )
        signpost_real = (
            data.get("signpost_real")
            if not is_update or "signpost_real" in data
            else getattr(self.instance, "signpost_real", None)
        )
        return parent, signpost_plan, signpost_real

    def _resolve_effective_device_type(self, data: dict, is_update: bool):
        """Resolve the effective device type, falling back to the instance value on updates.

        Args:
            data (dict): The validated data dictionary.
            is_update (bool): Whether the current operation is an update.

        Returns:
            The device type to use for validation.
        """
        device_type = data.get("device_type")
        if is_update and not device_type:
            return self.instance.device_type
        return device_type

    @staticmethod
    def _raise_parent_required_error() -> None:
        """Raise a ValidationError indicating that a parent is required.

        Raises:
            serializers.ValidationError: Always raised with a descriptive message.
        """
        raise serializers.ValidationError(
            {
                "parent": _(
                    "Parent is required for additional signs that are not ticket machines. "
                    "Set either parent (TrafficSign), signpost_plan, or signpost_real."
                )
            }
        )

    def validate(self, data: dict) -> dict:
        """Validate that parent is provided for non-ticket-machine device types.

        Args:
            data (dict): The validated data dictionary.

        Returns:
            dict: The validated data.

        Raises:
            serializers.ValidationError: If parent is missing for non-ticket-machine device types.
        """
        is_update = self._is_update()
        parent_in_data = "parent" in data
        signpost_parent_in_data = "signpost_plan" in data or "signpost_real" in data

        if is_update and not parent_in_data and not signpost_parent_in_data:
            return data

        parent, signpost_plan, signpost_real = self._resolve_effective_parents(data, is_update)
        device_type = self._resolve_effective_device_type(data, is_update)

        has_any_parent = bool(parent or signpost_plan or signpost_real)
        if not has_any_parent and device_type and device_type.code not in TICKET_MACHINE_CODES:
            self._raise_parent_required_error()

        return data


class ReplaceableDeviceInputSerializerMixin(metaclass=serializers.SerializerMetaclass):
    replaces = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID to the device plan that this device is replacing",
    )


class ReplaceableDeviceOutputSerializerMixin(metaclass=serializers.SerializerMetaclass):
    replaces = serializers.SerializerMethodField()
    replaced_by = serializers.SerializerMethodField()
    is_replaced = serializers.SerializerMethodField()

    def get_replaces(self, obj) -> Optional[UUID]:
        """ID of the device plan that this device plan has replaced"""
        replaces = obj.replaces
        return replaces.id if replaces else None

    def get_replaced_by(self, obj) -> Optional[UUID]:
        """ID of the device plan that has replaced this device plan"""
        replaced_by = obj.replaced_by
        return replaced_by.id if replaced_by else None

    def get_is_replaced(self, obj) -> bool:
        """Whether this device plan has been replaced by another device plan"""
        return obj.is_replaced


class StructuredContentValidator:
    """
    Validate structured content field against device type's content schema.
    Raises `ValidationError` if content is invalid.
    """

    requires_context = True

    def __call__(self, data: OrderedDict, serializer: serializers.Serializer):
        method = serializer.context["request"].method
        if method == "POST":
            content, device_type, missing_content = self.get_post_data(data)
        elif method in ("PUT", "PATCH"):
            content, device_type, missing_content = self.get_put_patch_data(data, serializer)

        self.validate_content(content, missing_content, device_type)

    def get_post_data(self, data: OrderedDict):
        content = data.get("content_s")
        device_type = data.get("device_type")
        missing_content = data.get("missing_content")
        return content, device_type, missing_content

    def get_put_patch_data(self, data: OrderedDict, serializer: serializers.Serializer):
        id = serializer.instance.id
        current_device = serializer.Meta.model.objects.get(id=id)
        content = data.get("content_s", current_device.content_s)
        device_type = data.get("device_type", current_device.device_type)
        missing_content = data.get("missing_content", current_device.missing_content)
        return content, device_type, missing_content

    def validate_content(self, content, missing_content, device_type):
        # Ignore missing content if `missing_content` is set.
        if content is None and missing_content:
            return

        if content is not None and missing_content:
            raise serializers.ValidationError(
                {
                    "missing_content": _(
                        "'Missing content' cannot be enabled when the content field (content_s) is not empty."
                    )
                }
            )

        validation_errors = validate_structured_content(content, device_type)

        if validation_errors:
            raised_errors = [message for e in validation_errors for message in e.messages]
            raise serializers.ValidationError({"content_s": raised_errors})


class TrafficControlDeviceTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    traffic_sign_type = serializers.SerializerMethodField(
        method_name="get_traffic_sign_type",
    )

    icons = serializers.SerializerMethodField(
        method_name="get_icon_urls",
        read_only=True,
        required=False,
    )

    class Meta:
        model = TrafficControlDeviceType
        fields = "__all__"

    @extend_schema_field(field=IconsType)
    def get_icon_urls(self, obj: TrafficControlDeviceType):
        icons = obj.get_icons()
        if not icons:
            return None
        return icons

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
