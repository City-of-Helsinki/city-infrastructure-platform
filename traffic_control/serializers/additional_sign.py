from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from ..models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
    AdditionalSignPlan,
    AdditionalSignReal,
    TrafficControlDeviceType,
)
from ..models.common import DeviceTypeTargetModel


class WritableNestedContentSerializerMixin:
    """
    Serializer mixin that adds support for writing nested content
    for additional sign plan and real serializers.
    """

    def create(self, validated_data):
        model = self.Meta.model
        content_model = self.Meta.content_model

        content_data = validated_data.pop("content", [])
        additional_sign = model.objects.create(**validated_data)
        common_content_data = {
            "parent": additional_sign,
            "created_by": additional_sign.created_by,
            "updated_by": additional_sign.updated_by,
        }

        for content in content_data:
            content.update(common_content_data)
            content_model.objects.create(**content)

        return additional_sign

    def update(self, instance, validated_data):
        content_model = self.Meta.content_model
        content_data = validated_data.pop("content", [])
        instance = super().update(instance, validated_data)
        request = self.context["request"]
        common_content_data = {
            "parent": instance,
            "updated_by": instance.updated_by,
        }

        if content_data or request.method == "PUT":
            # Delete all existing content related to the instance that is not in the request data.
            content_pks = [content["id"] for content in content_data if "id" in content]
            instance.content.exclude(pk__in=content_pks).delete()

        for content in content_data:
            pk = content.pop("id", None)
            content.update(common_content_data)

            # Update existing content instance if request data has an id for the content instance.
            # If id is not provided, a new content instance is created for the additional sign that
            # is being updated.
            if pk:
                instance.content.filter(pk=pk).update(**content)
            else:
                content.update({"created_by": request.user})
                content_model.objects.create(**content)

        return instance


class NestedAdditionalSignContentSerializerMixin:
    """
    Serializer mixin for nested AdditionalSignContent model serializers that
    handles the ID validation.
    """

    def validate_id(self, value):
        request = self.context["request"]

        # Nested content ID is not allowed on create
        if value and request.method == "POST":
            message = (
                "Creating new additional sign with pre-existing content instance "
                'is not allowed. Content objects must not have "id" defined.'
            )
            raise serializers.ValidationError(message)

        # Nested content ID must belong to an instance that is a child of the
        # additional sign instance that is being updated
        if value and request.method in ("PUT", "PATCH"):
            parent = self.Meta.model.objects.get(pk=value).parent
            parent_pk = self.context["view"].kwargs["pk"]

            if str(parent.pk) != parent_pk:
                message = (
                    "Updating content instances that do not belong to this additional sign "
                    "is not allowed."
                )
                raise serializers.ValidationError(message)

        return value


class AdditionalSignContentPlanSerializer(serializers.ModelSerializer):
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentPlan
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
        )


class NestedAdditionalSignContentPlanSerializer(
    NestedAdditionalSignContentSerializerMixin, serializers.ModelSerializer
):
    id = serializers.UUIDField(required=False)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentPlan
        exclude = ("parent",)
        read_only_fields = ("created_by", "updated_by", "created_at", "updated_at")


class AdditionalSignPlanSerializer(
    WritableNestedContentSerializerMixin,
    EnumSupportSerializerMixin,
    serializers.ModelSerializer,
):
    content = NestedAdditionalSignContentPlanSerializer(many=True, required=False)

    class Meta:
        model = AdditionalSignPlan
        content_model = AdditionalSignContentPlan
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "is_active", "deleted_at", "deleted_by")


class AdditionalSignPlanGeoJSONSerializer(AdditionalSignPlanSerializer):
    location = GeometryField(required=False)
    affect_area = GeometryField(required=False)


class AdditionalSignContentRealSerializer(serializers.ModelSerializer):
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentReal
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "updated_by",
        )


class NestedAdditionalSignContentRealSerializer(
    NestedAdditionalSignContentSerializerMixin, serializers.ModelSerializer
):
    id = serializers.UUIDField(required=False)
    device_type = serializers.PrimaryKeyRelatedField(
        queryset=TrafficControlDeviceType.objects.for_target_model(
            DeviceTypeTargetModel.ADDITIONAL_SIGN
        )
    )

    class Meta:
        model = AdditionalSignContentReal
        exclude = ("parent",)
        read_only_fields = ("created_by", "updated_by", "created_at", "updated_at")


class AdditionalSignRealSerializer(
    WritableNestedContentSerializerMixin,
    EnumSupportSerializerMixin,
    serializers.ModelSerializer,
):
    content = NestedAdditionalSignContentRealSerializer(many=True, required=False)

    class Meta:
        model = AdditionalSignReal
        content_model = AdditionalSignContentReal
        read_only_fields = (
            "created_by",
            "updated_by",
            "deleted_by",
            "deleted_at",
        )
        exclude = ("mount_type", "legacy_code", "is_active", "deleted_at", "deleted_by")


class AdditionalSignRealGeoJSONSerializer(AdditionalSignRealSerializer):
    location = GeometryField(required=False)
    affect_area = GeometryField(required=False)
