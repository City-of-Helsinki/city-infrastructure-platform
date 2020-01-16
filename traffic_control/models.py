import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA


class Structure(models.TextChoices):
    PORTAL = "PORTAL", _("Portal")
    POST = "POST", _("Post")
    WALL = "WALL", _("Wall")
    WIRE = "WIRE", _("Wire")
    BRIDGE = "BRIDGE", _("Bridge")
    OTHER = "OTHER", _("Other")


class InstallationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    COVERED = "COVERED", _("Covered")
    FALLEN = "FALLEN", _("Fallen")
    MISSING = "MISSING", _("Missing")
    OTHER = "OTHER", _("Other")


class Size(models.TextChoices):
    SMALL = "S", _("Small")
    MEDIUM = "M", _("Medium")
    LARGE = "L", _("Large")


class Surface(models.TextChoices):
    CONVEX = "CONVEX", _("Convex")
    DIRECT = "FLAT", _("Flat")


class Reflection(models.TextChoices):
    R1 = "R1", _("r1")
    R2 = "R2", _("r2")
    R3 = "R3", _("r3")


class Color(models.IntegerChoices):
    BLUE = 1, _("Blue")
    YELLOW = 2, _("Yellow")


class LocationSpecifier(models.IntegerChoices):
    RIGHT = 1, _("Right side")
    LEFT = 2, _("Left side")
    ABOVE = 3, _("Above")
    MIDDLE = 4, _("Middle")
    VERTICAL = 5, _("Vertical")
    OUTSIDE = 6, _("Outside")


class Condition(models.IntegerChoices):
    VERY_BAD = 1, _("Very bad")
    BAD = 2, _("Bad")
    AVERAGE = 3, _("Average")
    GOOD = 4, _("Good")
    VERY_GOOD = 5, _("Very good")


class TrafficSignCode(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    code = models.CharField(_("Code"), max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_code"
        verbose_name = _("Traffic Sign Code")
        verbose_name_plural = _("Traffic Sign Codes")

    def __str__(self):
        return "%s - %s" % (self.code, self.description)


class Lifecycle(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    status = models.CharField(_("Status"), max_length=32)
    description = models.CharField(
        _("Description"), max_length=254, blank=True, null=True
    )

    class Meta:
        db_table = "lifecycle"
        verbose_name = _("Lifecycle")
        verbose_name_plural = _("Lifecycles")

    def __str__(self):
        return "%s" % self.description


class TrafficSignPlan(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location_xy = models.PointField(_("Location (2D)"), srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0, blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    code = models.ForeignKey(
        TrafficSignCode, verbose_name=_("Traffic Sign Code"), on_delete=models.CASCADE
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    structure_id = models.IntegerField(_("Structure id"), blank=True, null=True)
    structure_type = models.CharField(
        _("Structure"),
        max_length=10,
        choices=Structure.choices,
        default=Structure.OTHER,
    )
    lifecycle = models.ForeignKey(
        Lifecycle, verbose_name=_("Lifecycle"), on_delete=models.CASCADE
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
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
    )
    plan_link = models.CharField(_("Plan link"), max_length=254, blank=True, null=True)
    size = models.CharField(
        _("Size"), max_length=1, choices=Size.choices, default=Size.MEDIUM
    )
    reflection_class = models.CharField(
        _("Reflection"), max_length=2, choices=Reflection.choices, default=Reflection.R1
    )
    surface_class = models.CharField(
        _("Surface"), max_length=6, choices=Surface.choices, default=Surface.DIRECT
    )
    color = models.IntegerField(_("Color"), choices=Color.choices, default=Color.BLUE)
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    location_specifier = models.IntegerField(
        _("Location specifier"),
        choices=LocationSpecifier.choices,
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
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
    location_xy = models.PointField(_("Location (2D)"), srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0, blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Real"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    code = models.ForeignKey(
        TrafficSignCode, verbose_name=_("Traffic Sign Code"), on_delete=models.CASCADE
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    structure_id = models.IntegerField(_("Structure id"), blank=True, null=True)
    structure_type = models.CharField(
        _("Structure"),
        max_length=10,
        choices=Structure.choices,
        default=Structure.OTHER,
    )
    lifecycle = models.ForeignKey(
        Lifecycle, verbose_name=_("Lifecycle"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
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
    manufacturer = models.CharField(
        _("Manufacturer"), max_length=254, blank=True, null=True
    )
    rfid = models.CharField(_("RFID"), max_length=254, blank=True, null=True)
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    installation_date = models.DateField(_("Installation date"))
    installation_status = models.CharField(
        _("Installation status"),
        max_length=10,
        choices=InstallationStatus.choices,
        default=InstallationStatus.ACTIVE,
    )
    installation_id = models.CharField(_("Installation id"), max_length=254)
    installation_details = models.CharField(
        _("Installation details"), max_length=254, blank=True, null=True
    )
    condition = models.IntegerField(
        _("Condition"), choices=Condition.choices, default=Condition.GOOD
    )
    allu_decision_id = models.CharField(_("Decision id (Allu)"), max_length=254)
    size = models.CharField(
        _("Size"), max_length=1, choices=Size.choices, default=Size.MEDIUM
    )
    reflection_class = models.CharField(
        _("Reflection"), max_length=2, choices=Reflection.choices, default=Reflection.R1
    )
    surface_class = models.CharField(
        _("Surface"), max_length=6, choices=Surface.choices, default=Surface.DIRECT
    )
    color = models.IntegerField(_("Color"), choices=Color.choices, default=Color.BLUE)
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    location_specifier = models.IntegerField(
        _("Location specifier"),
        choices=LocationSpecifier.choices,
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")

    def __str__(self):
        return "%s %s %s" % (self.id, self.code, self.value)
