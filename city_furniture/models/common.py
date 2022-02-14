import uuid
from typing import Optional

from auditlog.registry import auditlog
from colorfield.fields import ColorField
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from city_furniture.enums import (
    CityFurnitureClassType,
    CityFurnitureDeviceTypeTargetModel,
    CityFurnitureFunctionType,
    OrganizationLevel,
)
from traffic_control.mixins.models import SourceControlModel


class CityFurnitureDeviceTypeQuerySet(models.QuerySet):
    def for_target_model(self, target_model: CityFurnitureDeviceTypeTargetModel):
        return self.filter(Q(target_model=None) | Q(target_model=target_model))


class CityFurnitureDeviceType(models.Model):
    """
    A separate model from TrafficControlDeviceType is used, as these will contain overlapping device codes that
    come from two separate external sources.
    """

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    code = models.CharField(_("Code"), unique=True, max_length=32)
    class_type = EnumIntegerField(CityFurnitureClassType, verbose_name=_("City Furniture Class type"))
    function_type = EnumIntegerField(CityFurnitureFunctionType, verbose_name=_("City Furniture Function or Usage type"))
    icon = models.CharField(_("Icon"), max_length=100, blank=True)  # Icon of the actual device
    description = models.CharField(_("Description"), max_length=254, blank=True, null=True)
    size = models.CharField(_("Size"), max_length=50, blank=True)
    target_model = EnumField(
        CityFurnitureDeviceTypeTargetModel,
        verbose_name=_("Target data model"),
        max_length=32,
        blank=True,
        null=True,
    )

    objects = CityFurnitureDeviceTypeQuerySet.as_manager()

    class Meta:
        db_table = "city_furniture_device_type"
        verbose_name = _("City Furniture Device Type")
        verbose_name_plural = _("City Furniture Device Types")

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"

    def save(self, validate_target_model_change=True, *args, **kwargs) -> None:
        if self.pk:
            self.validate_change_target_model(self.target_model, raise_exception=validate_target_model_change)

        super().save(*args, **kwargs)

    def _has_invalid_related_models(self, target_type: CityFurnitureDeviceTypeTargetModel) -> bool:
        """
        Check if instance has related models that are invalid with given target
        type value.
        """
        relations = [
            "furnituresignpost",
        ]
        ignore_prefix = target_type.value.replace("_", "")
        relevant_relations = [relation for relation in relations if not relation.startswith(ignore_prefix)]

        related_pks = []
        queryset = CityFurnitureDeviceType.objects.filter(pk=self.pk).values_list(*relevant_relations)
        if queryset.exists():
            related_pks = queryset.first()

        return any(related_pks)

    def validate_change_target_model(
        self,
        new_target_type: Optional[CityFurnitureDeviceTypeTargetModel],
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

    def validate_relation(self, model: CityFurnitureDeviceTypeTargetModel) -> bool:
        """
        Validate that the related model is allowed to have relationship
        to this TrafficControlDeviceType instance.
        """
        if self.target_model and self.target_model is not model:
            return False

        return True


class CityFurnitureColor(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(_("Name"), max_length=64, unique=True)
    rgb = ColorField()

    class Meta:
        db_table = "city_furniture_color"
        verbose_name = _("City Furniture Color")
        verbose_name_plural = _("City Furniture Colors")

    def __str__(self):
        return self.name


class CityFurnitureTarget(SourceControlModel):
    """Details about the guided object target (Opastettava kohde) that city furniture devices are related to"""

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name_fi = models.CharField(_("Finnish name"), max_length=254)
    name_sw = models.CharField(_("Swedish name"), max_length=254, blank=True, null=True)
    name_en = models.CharField(_("English name"), max_length=254, blank=True, null=True)
    description = models.CharField(_("Description"), max_length=254, blank=True, null=True)

    class Meta:
        db_table = "city_furniture_target"
        verbose_name = _("City Furniture Target")
        verbose_name_plural = _("City Furniture Targets")


class ResponsibleEntity(models.Model):
    """
    Responsible Entity for a City Furniture Device

    Organization chain is most often the following:
    Toimiala > Palvelu > Henkilö
    e.g.
    KYMP > Yleiset Alueet > Matti Meikäläinen
    """

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name = models.CharField(_("Name"), max_length=254)
    organization_level = EnumIntegerField(
        OrganizationLevel,
        verbose_name=_("Organization level"),
        default=OrganizationLevel.PERSON,
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Responsible Entity"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "responsible_entity"
        verbose_name = _("Responsible Entity")
        verbose_name_plural = _("Responsible Entities")


auditlog.register(CityFurnitureDeviceType)
auditlog.register(CityFurnitureColor)
auditlog.register(CityFurnitureTarget)
