import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from traffic_control.mixins.models import SourceControlModel


class GroupOperationalArea(models.Model):
    """
    Model to link OperationalAreas to django.contrib.auth.Group model
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.OneToOneField(
        Group,
        unique=True,
        related_name="operational_area",
        on_delete=models.CASCADE,
    )
    areas = models.ManyToManyField(
        "OperationalArea",
        related_name="groups",
        blank=True,
    )

    class Meta:
        verbose_name = _("Group operational area")
        verbose_name_plural = _("Group operational areas")

    def __str__(self):
        return f"GroupOperationalArea {self.group.name}"


class OperationalArea(SourceControlModel):
    """
    Model containing operational area polygon used to check location based
    permissions
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Name"), max_length=256, blank=False)
    name_short = models.CharField(_("Name short"), max_length=256, blank=True)
    area_type = models.CharField(_("Area type"), max_length=256, blank=True)
    contractor = models.CharField(_("Contractor"), max_length=256, blank=True)
    start_date = models.DateField(_("Start date"), null=True, blank=True)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    updated_date = models.DateField(_("Updated date"), null=True, blank=True)
    task = models.CharField(_("Task"), max_length=256, blank=True)
    status = models.CharField(_("Status"), max_length=256, blank=True)
    location = models.MultiPolygonField(_("Location (3D)"), dim=3, srid=settings.SRID)

    class Meta:
        verbose_name = _("Operational area")
        verbose_name_plural = _("Operational areas")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"OperationalArea {self.name}"
