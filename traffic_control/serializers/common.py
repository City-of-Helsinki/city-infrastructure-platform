from typing import Optional, OrderedDict
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from enumfields.drf import EnumSupportSerializerMixin
from guardian.shortcuts import get_objects_for_user
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.mixins.models import AbstractFileModel
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


class PermissionFilteredRelatedField(serializers.Field):
    """
    A custom, read-only field that accepts a related manager,
    filters its queryset based on `is_public` and user permissions,
    and returns the serialized data.
    """

    def __init__(self, permission_codename: str, serializer_class, **kwargs):
        """
        :param permission_codename: The full permission string to check
                                    (e.g., "app.view_modelfile").
        :param serializer_class: The serializer class to use for the
                                 related objects (e.g., MyFileSerializer).
        """
        self.permission_codename = permission_codename
        self.serializer_class = serializer_class
        kwargs.setdefault(
            "help_text", "List of public and private attached files that the user has permission to view."
        )
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        """
        Converts the 'value' (a queryset manager, e.g., barrier_plan.files)
        into a primitive, serializable list of its filtered objects.
        """
        # Double-check we're dealing with a collection
        if not isinstance(value, models.Manager):
            raise TypeError(
                f"The attribute for the field '{self.field_name}' on serializer '{self.parent.__class__.__name__}'"
                f"is not a 'models.Manager' instance (basically a collection). It received a '{type(value).__name__}'"
                f"instead."
            )

        if not issubclass(value.model, AbstractFileModel):
            raise TypeError(
                f"The model '{value.model.__name__}' for the field '{self.field_name}' on serializer"
                f"'{self.parent.__class__.__name__}' does not inherit from 'AbstractFileModel'."
            )

        request = self.context.get("request")
        public_objects_qs = value.filter(is_public=True)

        if not request or not request.user or not request.user.is_authenticated:
            final_queryset = public_objects_qs
        else:
            user = request.user
            private_objects_qs = value.filter(is_public=False)
            viewable_private_objects_qs = get_objects_for_user(
                user,
                self.permission_codename,
                klass=private_objects_qs,
                accept_global_perms=True,
            )
            final_queryset = public_objects_qs | viewable_private_objects_qs
        return self.serializer_class(
            final_queryset,
            many=True,
            context=self.context,
        ).data
