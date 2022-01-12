import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from traffic_control.mixins.models import SourceControlModel
from traffic_control.models.common import Owner


class CoverageAreaCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(_("Name"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("Coverage area category")
        verbose_name_plural = _("Coverage area categories")

    def __str__(self):
        return self.name


class CoverageArea(SourceControlModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        CoverageAreaCategory,
        verbose_name=_("Category"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    area_type = models.CharField(_("Area type"), max_length=100, blank=True)
    season = models.CharField(_("Season"), max_length=100, blank=True)
    resident_parking_id = models.CharField(_("Resident parking id"), max_length=100, blank=True)
    place_position = models.CharField(_("Position"), max_length=100, blank=True)
    validity = models.CharField(_("Validity"), max_length=100, blank=True)
    duration = models.CharField(_("Duration"), max_length=100, blank=True)
    surface_area = models.FloatField(_("Surface area"), null=True, blank=True)
    parking_slots = models.IntegerField(_("Parking slots"), null=True, blank=True)
    additional_info = models.TextField(_("Additional info"), blank=True)
    stopping_prohibited = models.CharField(_("Stopping prohibited"), max_length=100, blank=True)
    updated_at = models.DateField(_("Updated at"), null=True, blank=True)
    owner = models.ForeignKey(Owner, verbose_name=_("Owner"), null=True, blank=True, on_delete=models.PROTECT)
    location = models.MultiPolygonField(_("Location (3D)"), dim=3, srid=settings.SRID)

    class Meta:
        verbose_name = _("Coverage area")
        verbose_name_plural = _("Coverage areas")

    def __str__(self):
        return f"{self.area_type} - f{self.source_id}"
