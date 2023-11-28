import uuid
from typing import Optional

import jsonschema
from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField

from traffic_control.enums import DeviceTypeTargetModel, TRAFFIC_SIGN_TYPE_MAP, TrafficControlDeviceTypeType


class JSONSchemaField(models.JSONField):
    """
    Field for saving valid json-schema objects.
    """

    empty_values = [None]

    def validate(self, value, model_instance):
        super().validate(value, model_instance)

        if not isinstance(value, dict):
            raise ValidationError(_("Schema must be type of JSON object"))

        meta_schema = jsonschema.Draft202012Validator.META_SCHEMA
        meta_validator = jsonschema.Draft202012Validator(meta_schema)

        validation_errors = []
        for error in meta_validator.iter_errors(value):
            message = error.message
            if error.path:
                # Add property path to the message
                message = ".".join(error.path) + ": " + message
            validation_errors.append(ValidationError(message))

        if validation_errors:
            # Remove duplicate validation errors
            validation_errors_unique = list(set(validation_errors))
            raise ValidationError(validation_errors_unique)


class TrafficControlDeviceTypeQuerySet(models.QuerySet):
    def for_target_model(self, target_model: DeviceTypeTargetModel):
        return self.filter(Q(target_model=None) | Q(target_model=target_model))


class TrafficControlDeviceType(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    code = models.CharField(
        _("Code"),
        unique=True,
        max_length=32,
        help_text=_("Standardised code of the device type."),
    )
    icon = models.CharField(
        _("Icon"),
        max_length=100,
        blank=True,
    )
    description = models.CharField(
        _("Description"),
        max_length=254,
        blank=True,
        null=True,
    )
    value = models.CharField(
        _("Value"),
        max_length=50,
        blank=True,
        help_text=_("Numeric value on the sign."),
    )
    unit = models.CharField(
        _("Unit"),
        max_length=50,
        blank=True,
        help_text=_("Unit, in which the numeric value is in."),
    )
    size = models.CharField(
        _("Size"),
        max_length=50,
        blank=True,
    )
    legacy_code = models.CharField(
        _("Legacy code"),
        max_length=32,
        blank=True,
        null=True,
    )
    legacy_description = models.CharField(
        _("Legacy description"),
        max_length=254,
        blank=True,
        null=True,
    )
    target_model = EnumField(
        DeviceTypeTargetModel,
        verbose_name=_("Target data model"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("Defines which model this device type describes."),
    )
    type = EnumField(
        TrafficControlDeviceTypeType,
        verbose_name=_("Type"),
        max_length=50,
        blank=True,
        null=True,
    )
    content_schema = JSONSchemaField(
        verbose_name=_("Content schema"),
        null=True,
        blank=True,
    )

    objects = TrafficControlDeviceTypeQuerySet.as_manager()

    class Meta:
        db_table = "traffic_control_device_type"
        verbose_name = _("Traffic Control Device Type")
        verbose_name_plural = _("Traffic Control Device Types")

    def __str__(self):
        return "%s - %s" % (self.code, self.description)

    def get_icons(self):
        """
        Get icon file paths for each type and size. File paths are based on the `icon` field,
        and it is not guaranteed that the file really exists.
        """
        if not self.icon:
            return None

        svg_name = self.icon
        png_name = f"{self.icon}.png"
        png_sizes = [32, 64, 128, 256]
        static_url = settings.STATIC_URL

        icons = {"svg": f"{static_url}traffic_control/svg/traffic_sign_icons/{svg_name}"}
        for size in png_sizes:
            icons[f"png_{size}"] = f"{static_url}traffic_control/png/traffic_sign_icons/{size}/{png_name}"

        return icons

    @property
    def traffic_sign_type(self):
        return TRAFFIC_SIGN_TYPE_MAP.get(self.code[0])

    def clean(self):
        self.validate_target_model_content_schema()

    def validate_target_model_content_schema(self):
        target_models_with_content_schema = (DeviceTypeTargetModel.ADDITIONAL_SIGN,)
        if (
            self.content_schema is not None
            and self.target_model is not None
            and self.target_model not in target_models_with_content_schema
        ):
            raise ValidationError(
                _("Target model '%(target_model)s' does not support content schema"),
                params={"target_model": self.target_model.label},
            )

    def save(self, validate_target_model_change=True, *args, **kwargs):
        if self.pk:
            self.validate_change_target_model(self.target_model, raise_exception=validate_target_model_change)

        super().save(*args, **kwargs)

    def _has_invalid_related_models(self, target_type: DeviceTypeTargetModel) -> bool:
        """
        Check if instance has related models that are invalid with given target
        type value.
        """
        relations = [
            "barrierplan",
            "barrierreal",
            "roadmarkingplan",
            "roadmarkingreal",
            "signpostplan",
            "signpostreal",
            "trafficlightplan",
            "trafficlightreal",
            "trafficsignplan",
            "trafficsignreal",
            "additionalsignplan",
            "additionalsignreal",
        ]
        ignore_prefix = target_type.value.replace("_", "")
        relevant_relations = [relation for relation in relations if not relation.startswith(ignore_prefix)]

        related_pks = []
        queryset = TrafficControlDeviceType.objects.filter(pk=self.pk).values_list(*relevant_relations)
        if queryset.exists():
            related_pks = queryset.first()

        return any(related_pks)

    def validate_change_target_model(
        self,
        new_target_type: Optional[DeviceTypeTargetModel],
        raise_exception: bool = False,
    ) -> bool:
        """
        Validate if instance target_model value can be changed to the given new_value.

        Validate that relations on other models do not become non-allowed after changing
        instance target_model to the new value.

        Returns boolean value indicating if change is valid or raises ValidationError if
        raise_exception is True
        """
        if not new_target_type:
            return True  # None is always valid value

        has_invalid_relations = self._has_invalid_related_models(new_target_type)

        if raise_exception and has_invalid_relations:
            raise ValidationError(
                f"Some traffic control devices related to this device type instance "
                f"will become invalid if target_model value is changed to "
                f"{new_target_type.value}. target_model can not be changed until this "
                f"is resolved."
            )

        return True

    def validate_relation(self, model: DeviceTypeTargetModel):
        """
        Validate that the related model is allowed to have relationship
        to this TrafficControlDeviceType instance.
        """
        if self.target_model and self.target_model is not model:
            return False

        return True


auditlog.register(TrafficControlDeviceType)
