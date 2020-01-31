import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _  # NOQA
from enumfields import Enum, EnumField, EnumIntegerField

from .common import Condition, InstallationStatus, Lifecycle


class BarrierType(Enum):
    BOOM = "BOOM"
    FENCE = "FENCE"
    FENCE_WITH_ARROW = "FENCE_WITH_ARROW"
    POLE = "POLE"
    POLE_LEFT_OF_LANE = "POLE_LEFT_OF_LANE"
    POLE_RIGHT_OF_LANE = "POLE_RIGHT_OF_LANE"
    CONE = "CONE"

    class Labels:
        BOOM = _("Boom")
        FENCE = _("Fence")
        FENCE_WITH_ARROW = _("Fence with arrow control")
        POLE = _("Pole")
        POLE_LEFT_OF_LANE = _("Pole, left side of the lane")
        POLE_RIGHT_OF_LANE = _("Pole, right side of the lane")
        CONE = _("Cone")


class ConnectionType(Enum):
    CLOSED = 1
    OPEN_OUT = 2

    class Labels:
        CLOSED = _("Closed")
        OPEN_OUT = _("Open out")


class Reflective(Enum):
    YES = "YES"
    NO = "NO"
    RED_YELLOW = "RED_YELLOW"

    class Labels:
        YES = _("Yes")
        NO = _("No")
        RED_YELLOW = _("Red-yellow")


class LaneType(Enum):
    MAIN = 1
    FAST = 2
    BUS = 3
    TURN_LEFT = 4

    class Labels:
        MAIN = _("Main lane")
        FAST = _("Fast lane")
        BUS = _("Bus lane")
        TURN_LEFT = _("Turn left lane")


class LocationSpecifier(Enum):
    MIDDLE = 1
    RIGHT = 2
    LEFT = 3

    class Labels:
        MIDDLE = _("Middle of road or lane")
        RIGHT = _("Right of road or lane")
        LEFT = _("Left of road or lane")


class BarrierPlan(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    type = EnumField(BarrierType, verbose_name=_("Barrier type"), max_length=20)
    connection_type = EnumIntegerField(
        ConnectionType, verbose_name=_("Connection type"), blank=True, null=True
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    is_electric = models.BooleanField(_("Is electric"), default=False)
    owner = models.CharField(_("Owner"), max_length=254, blank=True, null=True)
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
    )
    plan_link = models.CharField(_("Plan link"), max_length=254, blank=True, null=True)
    reflective = EnumField(
        Reflective, verbose_name=_("Reflective"), blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_barrier_plan_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_barrier_plan_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_barrier_plan_set",
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
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = EnumIntegerField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
        null=True,
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    count = models.IntegerField(_("Count"), blank=True, null=True)
    txt = models.TextField(_("Txt"), blank=True, null=True)

    class Meta:
        db_table = "barrier_plan"
        verbose_name = _("Barrier plan")
        verbose_name_plural = _("Barrier plans")

    def __str__(self):
        return "%s %s" % (self.id, self.type)


class BarrierReal(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    barrier_plan = models.ForeignKey(
        BarrierPlan,
        verbose_name=_("Barrier plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    type = EnumField(BarrierType, verbose_name=_("Barrier type"), max_length=20)
    connection_type = EnumIntegerField(
        ConnectionType, verbose_name=_("Connection type"), blank=True, null=True
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    is_electric = models.BooleanField(_("Is electric"), default=False)
    owner = models.CharField(_("Owner"), max_length=254, blank=True, null=True)
    installation_date = models.DateField(_("Installation date"))
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        default=InstallationStatus.IN_USE,
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    condition = EnumIntegerField(
        Condition, verbose_name=_("Condition"), default=Condition.GOOD
    )
    reflective = EnumField(
        Reflective, verbose_name=_("Reflective"), blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_barrier_real_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_barrier_real_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_barrier_real_set",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = EnumIntegerField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
        null=True,
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    count = models.IntegerField(_("Count"), blank=True, null=True)
    txt = models.TextField(_("Txt"), blank=True, null=True)

    class Meta:
        db_table = "barrier_real"
        verbose_name = _("Barrier real")
        verbose_name_plural = _("Barrier reals")

    def __str__(self):
        return "%s %s" % (self.id, self.type)
