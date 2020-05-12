import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from ..mixins.models import SoftDeleteModelMixin
from .common import Condition, InstallationStatus, Lifecycle, TrafficSignCode
from .mount import MountPlan, MountReal, MountType
from .utils import SoftDeleteQuerySet


class TrafficLightSoundBeaconValue(Enum):
    NO = 1
    YES = 2

    class Labels:
        NO = _("No")
        YES = _("Yes")


class LocationSpecifier(Enum):
    RIGHT = 1
    LEFT = 2
    ABOVE = 3
    MIDDLE = 4

    class Labels:
        RIGHT = _("Right side of road")
        LEFT = _("Left side of road")
        ABOVE = _("Above the road")
        MIDDLE = _("Middle of road")


class TrafficLightType(Enum):
    TRAFFIC_LIGHT = 1
    SOUND_BEACON = 2
    BUTTON = 3

    class Labels:
        TRAFFIC_LIGHT = _("Traffic light")
        SOUND_BEACON = _("Sound beacon")
        BUTTON = _("Button")


class TrafficLightPlan(SoftDeleteModelMixin, models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.PointField(_("Location (2D)"), srid=settings.SRID)
    direction = models.IntegerField(_("Direction"), default=0)
    type = EnumIntegerField(TrafficLightType, blank=True, null=True)
    code = models.ForeignKey(
        TrafficSignCode, verbose_name=_("Traffic Sign Code"), on_delete=models.CASCADE
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    mount_type = EnumField(
        MountType,
        verbose_name=_("Mount type"),
        max_length=20,
        default=MountType.POST,
        blank=True,
        null=True,
    )
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_traffic_light_plan_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_traffic_light_plan_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_traffic_light_plan_set",
        on_delete=models.CASCADE,
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
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    sound_beacon = EnumIntegerField(
        TrafficLightSoundBeaconValue,
        verbose_name=_("Sound beacon"),
        blank=True,
        null=True,
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    lane_number = models.IntegerField(_("Lane number"), blank=True, null=True)
    lane_type = models.IntegerField(_("Lane type"), blank=True, null=True)
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    owner = models.CharField(_("Owner"), max_length=254)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "traffic_light_plan"
        verbose_name = _("Traffic Light Plan")
        verbose_name_plural = _("Traffic Light Plans")

    def __str__(self):
        return "%s %s %s" % (self.id, self.type, self.code)


class TrafficLightPlanFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="planfiles/traffic_light/"
    )
    traffic_light_plan = models.ForeignKey(
        TrafficLightPlan, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "traffic_light_plan_file"
        verbose_name = _("Traffic Light Plan File")
        verbose_name_plural = _("Traffic Light Plan Files")

    def __str__(self):
        return "%s" % self.file


class TrafficLightReal(SoftDeleteModelMixin, models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    traffic_light_plan = models.ForeignKey(
        TrafficLightPlan,
        verbose_name=_("Traffic Light Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    location = models.PointField(_("Location (2D)"), srid=settings.SRID)
    direction = models.IntegerField(_("Direction"), default=0)
    type = EnumIntegerField(TrafficLightType, blank=True, null=True)
    code = models.ForeignKey(
        TrafficSignCode, verbose_name=_("Traffic Sign Code"), on_delete=models.CASCADE
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    mount_type = EnumField(
        MountType,
        verbose_name=_("Mount type"),
        max_length=20,
        default=MountType.POST,
        blank=True,
        null=True,
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
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_traffic_light_real_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_traffic_light_real_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_traffic_light_real_set",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        default=Condition.VERY_GOOD,
        blank=True,
        null=True,
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
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    sound_beacon = EnumIntegerField(
        TrafficLightSoundBeaconValue,
        verbose_name=_("Sound beacon"),
        blank=True,
        null=True,
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    owner = models.CharField(_("Owner"), max_length=254)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "traffic_light_real"
        verbose_name = _("Traffic Light Real")
        verbose_name_plural = _("Traffic Light Reals")

    def __str__(self):
        return "%s %s %s" % (self.id, self.type, self.code)


class TrafficLightRealFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="realfiles/traffic_light/"
    )
    traffic_light_real = models.ForeignKey(
        TrafficLightReal, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "traffic_light_real_file"
        verbose_name = _("Traffic Light Real File")
        verbose_name_plural = _("Traffic Light Real Files")

    def __str__(self):
        return f"{self.file}"


auditlog.register(TrafficLightPlan)
auditlog.register(TrafficLightReal)
