import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA
from enumfields import Enum, EnumField, EnumIntegerField


class Mount(Enum):
    PORTAL = "PORTAL"
    POST = "POST"
    WALL = "WALL"
    WIRE = "WIRE"
    BRIDGE = "BRIDGE"
    OTHER = "OTHER"

    class Labels:
        PORTAL = _("Portal")
        POST = _("Post")
        WALL = _("Wall")
        WIRE = _("Wire")
        BRIDGE = _("Bridge")
        OTHER = _("Other")


class InstallationStatus(Enum):
    ACTIVE = "ACTIVE"
    COVERED = "COVERED"
    FALLEN = "FALLEN"
    MISSING = "MISSING"
    OTHER = "OTHER"

    class Labels:
        ACTIVE = _("Active")
        COVERED = _("Covered")
        FALLEN = _("Fallen")
        MISSING = _("Missing")
        OTHER = _("Other")


class Size(Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"

    class Labels:
        SMALL = _("Small")
        MEDIUM = _("Medium")
        LARGE = _("Large")


class Surface(Enum):
    CONVEX = "CONVEX"
    FLAT = "FLAT"

    class Labels:
        CONVEX = _("Convex")
        FLAT = _("Flat")


class Reflection(Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"

    class Labels:
        R1 = _("r1")
        R2 = _("r2")
        R3 = _("r3")


class Color(Enum):
    BLUE = 1
    YELLOW = 2

    class Labels:
        BLUE = _("Blue")
        YELLOW = _("Yellow")


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


class Condition(Enum):
    VERY_BAD = 1
    BAD = 2
    AVERAGE = 3
    GOOD = 4
    VERY_GOOD = 5

    class Labels:
        VERY_BAD = _("Very bad")
        BAD = _("Bad")
        AVERAGE = _("Average")
        GOOD = _("Good")
        VERY_GOOD = _("Very good")


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
    mount_id = models.IntegerField(_("Mount id"), blank=True, null=True)
    mount_type = EnumField(
        Mount, verbose_name=_("Mount"), max_length=10, default=Mount.OTHER
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
    size = EnumField(Size, verbose_name=_("Size"), max_length=1, default=Size.MEDIUM)
    reflection_class = EnumField(
        Reflection, verbose_name=_("Reflection"), max_length=2, default=Reflection.R1
    )
    surface_class = EnumField(
        Surface, verbose_name=_("Surface"), max_length=6, default=Surface.FLAT
    )
    color = EnumIntegerField(Color, verbose_name=_("Color"), default=Color.BLUE)
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
    mount_id = models.IntegerField(_("Mount id"), blank=True, null=True)
    mount_type = EnumField(
        Mount, verbose_name=_("Mount"), max_length=10, default=Mount.OTHER
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
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        default=InstallationStatus.ACTIVE,
    )
    installation_id = models.CharField(_("Installation id"), max_length=254)
    installation_details = models.CharField(
        _("Installation details"), max_length=254, blank=True, null=True
    )
    condition = EnumIntegerField(
        Condition, verbose_name=_("Condition"), default=Condition.GOOD
    )
    allu_decision_id = models.CharField(_("Decision id (Allu)"), max_length=254)
    size = EnumField(Size, verbose_name=_("Size"), max_length=1, default=Size.MEDIUM)
    reflection_class = EnumField(
        Reflection, verbose_name=_("Reflection"), max_length=2, default=Reflection.R1
    )
    surface_class = EnumField(
        Surface, verbose_name=_("Surface"), max_length=6, default=Surface.FLAT
    )
    color = EnumIntegerField(Color, verbose_name=_("Color"), default=Color.BLUE)
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
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")

    def __str__(self):
        return "%s %s %s" % (self.id, self.code, self.value)
