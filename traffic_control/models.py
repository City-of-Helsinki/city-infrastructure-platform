import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA


class TrafficSignCode(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    code = models.CharField(_("Code"), max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )


class Lifecycle(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    status = models.CharField(_("Status"), max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )


class Size(models.TextChoices):
    SMALL = "S", _("Small")
    MEDIUM_LARGE = "M", _("Medium large")
    LARGE = "L", _("Large")


class Surface(models.TextChoices):
    CONVEX = "CV", _("Convex")
    DIRECT = "DR", _("Direct")


class Color(models.TextChoices):
    BLUE = "BL", _("Blue")
    YELLOW = "YE", _("Yellow")


class TrafficSignPlan(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location_xy = models.PointField(_("Location (2D)"), srid=settings.SRID)
    location_z = models.DecimalField(
        _("Location Z"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    direction = models.DecimalField(
        _("Direction"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    parent = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)
    decision_date = models.DateField(_("Decision date"))
    code = models.ForeignKey("TrafficSignCode", on_delete=models.CASCADE)
    value = models.CharField(
        _("TrafficSignCode value"), max_length=32, blank=True, null=True
    )
    lifecycle = models.ForeignKey("Lifecycle", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        related_name="created_by_trafficsignplan_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        related_name="updated_by_trafficsignplan_set",
        on_delete=models.CASCADE,
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254, blank=True, null=True)
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    decision_link = models.CharField(
        _("Decision link"), max_length=254, blank=True, null=True
    )
    plan_link = models.CharField(_("Plan link"), max_length=254, blank=True, null=True)
    size = models.CharField(
        max_length=1, choices=Size.choices, default=Size.MEDIUM_LARGE,
    )
    reflection_class = models.CharField(
        _("Reflection class"), max_length=32, blank=True, null=True
    )
    surface_class = models.CharField(
        max_length=2, choices=Surface.choices, default=Surface.DIRECT,
    )
    color = models.CharField(max_length=2, choices=Color.choices, default=Color.BLUE,)
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    location_specifier = models.IntegerField(
        _("Location specifier"), blank=True, null=True
    )

    def __str__(self):
        return "%s %s" % (self.id, self.code)
