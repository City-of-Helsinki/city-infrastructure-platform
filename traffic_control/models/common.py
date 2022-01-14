import uuid
from typing import Optional

from auditlog.registry import auditlog
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField

from traffic_control.enums import DeviceTypeTargetModel, TRAFFIC_SIGN_TYPE_MAP, TrafficControlDeviceTypeType
from traffic_control.mixins.models import UserControlModel


class Owner(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name_fi = models.CharField(verbose_name=_("Name (fi)"), max_length=254)
    name_en = models.CharField(verbose_name=_("Name (en)"), max_length=254)

    class Meta:
        verbose_name = _("Owner")
        verbose_name_plural = _("Owners")

    def __str__(self):
        return f"{self.name_en} ({self.name_fi})"


class TrafficControlDeviceTypeQuerySet(models.QuerySet):
    def for_target_model(self, target_model: DeviceTypeTargetModel):
        return self.filter(Q(target_model=None) | Q(target_model=target_model))


class TrafficControlDeviceType(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    code = models.CharField(_("Code"), unique=True, max_length=32)
    icon = models.CharField(_("Icon"), max_length=100, blank=True)
    description = models.CharField(_("Description"), max_length=254, blank=True, null=True)
    value = models.CharField(_("Value"), max_length=50, blank=True)
    unit = models.CharField(_("Unit"), max_length=50, blank=True)
    size = models.CharField(_("Size"), max_length=50, blank=True)
    legacy_code = models.CharField(_("Legacy code"), max_length=32, blank=True, null=True)
    legacy_description = models.CharField(_("Legacy description"), max_length=254, blank=True, null=True)
    target_model = EnumField(
        DeviceTypeTargetModel,
        verbose_name=_("Target data model"),
        max_length=32,
        blank=True,
        null=True,
    )
    type = EnumField(
        TrafficControlDeviceTypeType,
        verbose_name=_("Type"),
        max_length=50,
        blank=True,
        null=True,
    )

    objects = TrafficControlDeviceTypeQuerySet.as_manager()

    class Meta:
        db_table = "traffic_control_device_type"
        verbose_name = _("Traffic Control Device Type")
        verbose_name_plural = _("Traffic Control Device Types")

    def __str__(self):
        return "%s - %s" % (self.code, self.description)

    @property
    def traffic_sign_type(self):
        return TRAFFIC_SIGN_TYPE_MAP.get(self.code[0])

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
            "additionalsigncontentplan",
            "additionalsigncontentreal",
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


class OperationType(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    traffic_sign = models.BooleanField(_("Traffic sign"), default=False)
    additional_sign = models.BooleanField(_("Additional sign"), default=False)
    road_marking = models.BooleanField(_("Road marking"), default=False)
    barrier = models.BooleanField(_("Barrier"), default=False)
    signpost = models.BooleanField(_("Signpost"), default=False)
    traffic_light = models.BooleanField(_("Traffic light"), default=False)
    mount = models.BooleanField(_("Mount"), default=False)

    class Meta:
        verbose_name = _("Operation type")
        verbose_name_plural = _("Operation types")

    def __str__(self):
        return self.name


class OperationBase(UserControlModel):
    operation_date = models.DateField(_("Operation date"))
    straightness_value = models.FloatField(_("Straightness value"), null=True, blank=True)
    quality_requirements_fulfilled = models.BooleanField(_("Quality requirements fulfilled"), default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.operation_type} {self.operation_date}"
