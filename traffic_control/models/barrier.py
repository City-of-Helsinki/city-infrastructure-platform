import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from ..mixins.models import (
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from .common import (
    Condition,
    DeviceTypeTargetModel,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    TrafficControlDeviceType,
)
from .plan import Plan
from .utils import SoftDeleteQuerySet


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


class LocationSpecifier(Enum):
    MIDDLE = 1
    RIGHT = 2
    LEFT = 3

    class Labels:
        MIDDLE = _("Middle of road or lane")
        RIGHT = _("Right of road or lane")
        LEFT = _("Left of road or lane")


class BarrierPlan(
    UpdatePlanLocationMixin, SourceControlModel, SoftDeleteModel, UserControlModel
):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.BARRIER)
        ),
    )
    connection_type = EnumIntegerField(
        ConnectionType, verbose_name=_("Connection type"), default=ConnectionType.CLOSED
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    is_electric = models.BooleanField(_("Is electric"), default=False)
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
    )
    reflective = EnumField(
        Reflective, verbose_name=_("Reflective"), blank=True, null=True
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="barrier_plans",
        blank=True,
        null=True,
    )
    road_name = models.CharField(_("Road name"), max_length=254)
    lane_number = EnumField(
        LaneNumber,
        verbose_name=_("Lane number"),
        default=LaneNumber.MAIN_1,
        blank=True,
    )
    lane_type = EnumField(
        LaneType, verbose_name=_("Lane type"), default=LaneType.MAIN, blank=True,
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
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    count = models.IntegerField(_("Count"), blank=True, null=True)
    txt = models.TextField(_("Txt"), blank=True, null=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "barrier_plan"
        verbose_name = _("Barrier Plan")
        verbose_name_plural = _("Barrier Plans")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.BARRIER):
            raise ValidationError(
                f'Device type "{self.device_type}" is not allowed for barriers'
            )

        super().save(*args, **kwargs)


class BarrierPlanFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="planfiles/barrier/"
    )
    barrier_plan = models.ForeignKey(
        BarrierPlan, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "barrier_plan_file"
        verbose_name = _("Barrier Plan File")
        verbose_name_plural = _("Barrier Plan Files")

    def __str__(self):
        return "%s" % self.file


class BarrierReal(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    barrier_plan = models.ForeignKey(
        BarrierPlan,
        verbose_name=_("Barrier Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.BARRIER)
        ),
    )
    connection_type = EnumIntegerField(
        ConnectionType, verbose_name=_("Connection type"), default=ConnectionType.CLOSED
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    is_electric = models.BooleanField(_("Is electric"), default=False)
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
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
    reflective = EnumField(
        Reflective, verbose_name=_("Reflective"), blank=True, null=True
    )
    road_name = models.CharField(_("Road name"), max_length=254)
    lane_number = EnumField(
        LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True
    )
    lane_type = EnumField(
        LaneType, verbose_name=_("Lane type"), default=LaneType.MAIN, blank=True,
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
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    count = models.IntegerField(_("Count"), blank=True, null=True)
    txt = models.TextField(_("Txt"), blank=True, null=True)
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        default=Condition.VERY_GOOD,
        blank=True,
        null=True,
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "barrier_real"
        verbose_name = _("Barrier real")
        verbose_name_plural = _("Barrier reals")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.BARRIER):
            raise ValidationError(
                f'Device type "{self.device_type}" is not allowed for barriers'
            )

        super().save(*args, **kwargs)


class BarrierRealFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="realfiles/barrier/"
    )
    barrier_real = models.ForeignKey(
        BarrierReal, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "barrier_real_file"
        verbose_name = _("Barrier Real File")
        verbose_name_plural = _("Barrier Real Files")

    def __str__(self):
        return f"{self.file}"


auditlog.register(BarrierPlan)
auditlog.register(BarrierReal)
