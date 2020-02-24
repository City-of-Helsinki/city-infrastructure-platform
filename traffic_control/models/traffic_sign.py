import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA
from enumfields import Enum, EnumField, EnumIntegerField

from .common import (
    Color,
    Condition,
    InstallationStatus,
    Lifecycle,
    Reflection,
    Size,
    Surface,
    TrafficSignCode,
)
from .mount import MountPlan, MountReal


class LocationSpecifier(Enum):
    RIGHT = 1
    LEFT = 2
    ABOVE = 3
    MIDDLE = 4
    VERTICAL = 5
    OUTSIDE = 6

    class Labels:
        RIGHT = _("Right side")
        LEFT = _("Left side")
        ABOVE = _("Above")
        MIDDLE = _("Middle")
        VERTICAL = _("Vertical")
        OUTSIDE = _("Outside")


class TrafficSignPlan(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.PointField(_("Location (2D)"), srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0)
    code = models.ForeignKey(
        TrafficSignCode, verbose_name=_("Traffic Sign Code"), on_delete=models.CASCADE
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    order = models.IntegerField(_("Order"), default=1)
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    mount_type = models.CharField(_("Mount"), max_length=254, blank=True, null=True)
    mount_type_fi = models.CharField(
        _("Mount (fi)"), max_length=254, blank=True, null=True
    )
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
    )
    plan_link = models.CharField(_("Plan link"), max_length=254, blank=True, null=True)
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_traffic_sign_plan_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_traffic_sign_plan_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_traffic_sign_plan_set",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    size = EnumField(
        Size,
        verbose_name=_("Size"),
        max_length=1,
        default=Size.MEDIUM,
        blank=True,
        null=True,
    )
    reflection_class = EnumField(
        Reflection,
        verbose_name=_("Reflection"),
        max_length=2,
        default=Reflection.R1,
        blank=True,
        null=True,
    )
    surface_class = EnumField(
        Surface,
        verbose_name=_("Surface"),
        max_length=6,
        default=Surface.FLAT,
        blank=True,
        null=True,
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254)
    color = EnumIntegerField(
        Color, verbose_name=_("Color"), default=Color.BLUE, blank=True, null=True
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    source_id = models.CharField(_("Source id"), max_length=64, blank=True, null=True)
    source_name = models.CharField(
        _("Source name"), max_length=254, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_plan"
        verbose_name = _("Traffic Sign Plan")
        verbose_name_plural = _("Traffic Sign Plans")

    def __str__(self):
        return "%s %s %s" % (self.id, self.code, self.value)


class TrafficSignReal(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Traffic Sign Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    location = models.PointField(_("Location (2D)"), srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=20, decimal_places=6, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0)
    code = models.ForeignKey(
        TrafficSignCode,
        verbose_name=_("Traffic Sign Code"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    legacy_code = models.CharField(
        _("Legacy Traffic Sign Code"), max_length=32, blank=True, null=True
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Real"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    order = models.IntegerField(_("Order"), default=1)
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    mount_type = models.CharField(_("Mount"), max_length=254, blank=True, null=True)
    mount_type_fi = models.CharField(
        _("Mount (fi)"), max_length=254, blank=True, null=True
    )
    installation_date = models.DateField(_("Installation date"), blank=True, null=True)
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        default=InstallationStatus.IN_USE,
        blank=True,
        null=True,
    )
    installation_id = models.CharField(
        _("Installation id"), max_length=254, blank=True, null=True
    )
    installation_details = models.CharField(
        _("Installation details"), max_length=254, blank=True, null=True
    )
    allu_decision_id = models.CharField(
        _("Decision id (Allu)"), max_length=254, blank=True, null=True
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        default=Condition.VERY_GOOD,
        blank=True,
        null=True,
    )
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    scanned_at = models.DateTimeField(_("Scanned at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_traffic_sign_real_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_traffic_sign_real_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_traffic_sign_real_set",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    size = EnumField(
        Size,
        verbose_name=_("Size"),
        max_length=1,
        default=Size.MEDIUM,
        blank=True,
        null=True,
    )
    reflection_class = EnumField(
        Reflection,
        verbose_name=_("Reflection"),
        max_length=2,
        default=Reflection.R1,
        blank=True,
        null=True,
    )
    surface_class = EnumField(
        Surface,
        verbose_name=_("Surface"),
        max_length=6,
        default=Surface.FLAT,
        blank=True,
        null=True,
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254)
    manufacturer = models.CharField(
        _("Manufacturer"), max_length=254, blank=True, null=True
    )
    rfid = models.CharField(_("RFID"), max_length=254, blank=True, null=True)
    color = EnumIntegerField(
        Color, verbose_name=_("Color"), default=Color.BLUE, blank=True, null=True
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    source_id = models.CharField(_("Source id"), max_length=64, blank=True, null=True)
    source_name = models.CharField(
        _("Source name"), max_length=254, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")

    def __str__(self):
        return "%s %s %s" % (self.id, self.code, self.value)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = (
                TrafficSignCode.objects.filter(legacy_code=self.legacy_code)
                .order_by("code")
                .first()
            )
        super().save(*args, **kwargs)


auditlog.register(TrafficSignPlan)
auditlog.register(TrafficSignReal)
