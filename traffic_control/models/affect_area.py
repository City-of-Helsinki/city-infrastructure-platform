import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from traffic_control.mixins.models import SourceControlModel
from traffic_control.models.common import Owner


class ParkingAreaCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = _("parking area category")
        verbose_name_plural = _("parking area categories")

    def __str__(self):
        return self.name


class ParkingArea(SourceControlModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        ParkingAreaCategory,
        verbose_name=_("category"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    area_type = models.CharField(_("area type"), max_length=100, blank=True)
    season = models.CharField(_("season"), max_length=100, blank=True)
    resident_parking_id = models.CharField(
        _("resident parking id"), max_length=100, blank=True
    )
    place_position = models.CharField(_("position"), max_length=100, blank=True)
    validity = models.CharField(_("validity"), max_length=100, blank=True)
    duration = models.CharField(_("duration"), max_length=100, blank=True)
    surface_area = models.FloatField(_("surface area"), null=True, blank=True)
    parking_slots = models.IntegerField(_("parking slots"), null=True, blank=True)
    additional_info = models.TextField(_("additional info"), blank=True)
    stopping_prohibited = models.CharField(
        _("stopping prohibited"), max_length=100, blank=True
    )
    updated_at = models.DateField(_("updated at"), null=True, blank=True)
    owner = models.ForeignKey(
        Owner, verbose_name=_("owner"), null=True, blank=True, on_delete=models.PROTECT
    )
    location = models.MultiPolygonField(_("location"), srid=settings.SRID)

    def __str__(self):
        return f"{self.area_type} - f{self.source_id}"
