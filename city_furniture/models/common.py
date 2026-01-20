import os
import uuid
from typing import Optional

from auditlog.registry import auditlog
from colorfield.fields import ColorField
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage, storages
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from city_furniture.enums import CityFurnitureClassType, CityFurnitureDeviceTypeTargetModel, CityFurnitureFunctionType
from cityinfra import settings
from traffic_control.mixins.models import AbstractFileModel, SourceControlModel
from traffic_control.models.common import AbstractDeviceTypeMixin


class CityFurnitureDeviceTypeQuerySet(models.QuerySet):
    def for_target_model(self, target_model: CityFurnitureDeviceTypeTargetModel):
        return self.filter(Q(target_model=None) | Q(target_model=target_model))


def city_furniture_device_type_icon_storage() -> Storage:
    return storages["icons"]


class CityFurnitureDeviceTypeIcon(AbstractFileModel):
    file = models.FileField(
        _("File"),
        blank=False,
        null=False,
        unique=True,
        upload_to=settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION,
        # NOTE (2025-09-10 thiago)
        # We need to pass our storage as a callback that returns the target storage. If we don't the generated migration
        # will contain runtime server settings used when running migrations generation. This would mean either
        # 1) The migration produces an incorrectly configured field for production
        #    or
        # 2) The migration leaks the production keys into git via the generated migrations file
        storage=city_furniture_device_type_icon_storage,
    )

    class Meta:
        db_table = "city_furniture_device_type_icon"
        verbose_name = _("City Furniture Device Type Icon")
        verbose_name_plural = _("City Furniture Device Type Icons")


auditlog.register(CityFurnitureDeviceTypeIcon)


class CityFurnitureDeviceType(models.Model, AbstractDeviceTypeMixin):
    """
    A separate model from TrafficControlDeviceType is used, as these will contain overlapping device codes that
    come from two separate external sources.
    """

    SVG_ICON_DESTINATION = settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION
    PNG_ICON_DESTINATION = settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    code = models.CharField(
        _("Code"),
        unique=True,
        max_length=32,
        help_text=_("Code of the Device Type in the Helsinki Design Manual."),
    )
    class_type = EnumIntegerField(
        CityFurnitureClassType,
        verbose_name=_("City Furniture Class type"),
        help_text=_("OGC CityGML City Furniture Class"),
    )
    function_type = EnumIntegerField(
        CityFurnitureFunctionType,
        verbose_name=_("City Furniture Function or Usage type"),
        help_text=_("OGC CityGML City Furniture Function or Usage type"),
    )
    icon_file = models.ForeignKey(
        CityFurnitureDeviceTypeIcon,
        verbose_name=_("Icon file"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Icon of the actual device"),
    )
    description_fi = models.CharField(
        _("Finnish Description"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Description of the Device Type in Finnish."),
    )
    description_sw = models.CharField(
        _("Swedish Description"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Description of the Device Type in Swedish."),
    )
    description_en = models.CharField(
        _("English Description"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Description of the Device Type in English."),
    )
    size = models.CharField(
        _("Size"),
        max_length=50,
        blank=True,
        help_text=_("Standard size of the Device Type."),
    )
    target_model = EnumField(
        CityFurnitureDeviceTypeTargetModel,
        verbose_name=_("Target data model"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("City Furniture model that this Device Type is usable for."),
    )

    objects = CityFurnitureDeviceTypeQuerySet.as_manager()

    class Meta:
        db_table = "city_furniture_device_type"
        verbose_name = _("City Furniture Device Type")
        verbose_name_plural = _("City Furniture Device Types")

    def __str__(self) -> str:
        return f"{self.code} - {self.description_fi}"

    @property
    def icon_name(self):
        """Return just the name of the file without full path"""
        return os.path.basename(self.icon_file.file.name) if self.icon_file else ""

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
            "furnituresignpostplan",
            "furnituresignpostreal",
        ]
        ignore_prefix = target_type.value.replace("_", "")
        relevant_relations = [relation for relation in relations if not relation.startswith(ignore_prefix)]

        related_pks = []
        if relevant_relations:
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
                f"Some city furniture devices related to this device type instance "
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
    name = models.CharField(
        _("Name"),
        max_length=64,
        unique=True,
        help_text=_("Name of the color in Helsinki Design System or Manual."),
    )
    rgb = ColorField(
        help_text=_("RGB Hex value of the color"),
    )

    class Meta:
        db_table = "city_furniture_color"
        verbose_name = _("City Furniture Color")
        verbose_name_plural = _("City Furniture Colors")

    def __str__(self):
        return self.name


class CityFurnitureTarget(SourceControlModel):
    """Details about the guided object target (Opastettava kohde) that city furniture devices are related to"""

    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    name_fi = models.CharField(
        _("Finnish name"),
        max_length=254,
        help_text=_("Name of the target in Finnish."),
    )
    name_sw = models.CharField(
        _("Swedish name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the target in Swedish."),
    )
    name_en = models.CharField(
        _("English name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the target in English."),
    )
    description = models.CharField(
        _("Description"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Description of the target."),
    )

    class Meta:
        db_table = "city_furniture_target"
        verbose_name = _("City Furniture Target")
        verbose_name_plural = _("City Furniture Targets")

    def __str__(self):
        return self.name_fi


auditlog.register(CityFurnitureDeviceType)
auditlog.register(CityFurnitureColor)
auditlog.register(CityFurnitureTarget)
