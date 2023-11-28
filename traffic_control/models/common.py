import uuid

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

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


class OperationType(models.Model):
    name = models.CharField(_("Name"), max_length=200, help_text=_("Name of the operation."))
    traffic_sign = models.BooleanField(_("Traffic sign"), default=False)
    additional_sign = models.BooleanField(_("Additional sign"), default=False)
    road_marking = models.BooleanField(_("Road marking"), default=False)
    barrier = models.BooleanField(_("Barrier"), default=False)
    signpost = models.BooleanField(_("Signpost"), default=False)
    traffic_light = models.BooleanField(_("Traffic light"), default=False)
    furniture_signpost = models.BooleanField(_("Furniture signpost"), default=False)
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
