from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.enums import DeviceTypeTargetModel, LaneNumber, LaneType
from traffic_control.mixins.models import (
    AbstractFileModel,
    InstalledDeviceModel,
    OwnedDeviceModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.common import OperationBase, OperationType, TrafficControlDeviceType
from traffic_control.models.plan import Plan


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


class AbstractBarrier(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    location = models.GeometryField(_("Location (3D)"), dim=3, srid=settings.SRID)
    road_name = models.CharField(_("Road name"), max_length=254)
    lane_number = EnumField(LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True)
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.BARRIER)),
    )
    connection_type = EnumIntegerField(ConnectionType, verbose_name=_("Connection type"), default=ConnectionType.CLOSED)
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    is_electric = models.BooleanField(_("Is electric"), default=False)
    reflective = EnumField(Reflective, verbose_name=_("Reflective"), blank=True, null=True)
    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)
    length = models.IntegerField(_("Length"), blank=True, null=True)
    count = models.IntegerField(_("Count"), blank=True, null=True)
    txt = models.TextField(_("Txt"), blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.BARRIER):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for barriers')

        super().save(*args, **kwargs)


class BarrierPlan(UpdatePlanLocationMixin, AbstractBarrier):
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="barrier_plans",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "barrier_plan"
        verbose_name = _("Barrier Plan")
        verbose_name_plural = _("Barrier Plans")
        unique_together = ["source_name", "source_id"]


class BarrierReal(AbstractBarrier, InstalledDeviceModel):
    barrier_plan = models.ForeignKey(
        BarrierPlan,
        verbose_name=_("Barrier Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "barrier_real"
        verbose_name = _("Barrier real")
        verbose_name_plural = _("Barrier reals")
        unique_together = ["source_name", "source_id"]


class BarrierRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"barrier": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    barrier_real = models.ForeignKey(
        BarrierReal,
        verbose_name=_("barrier real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "barrier_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Barrier real operation")
        verbose_name_plural = _("Barrier real operations")


class BarrierPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/barrier/")
    barrier_plan = models.ForeignKey(BarrierPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "barrier_plan_file"
        verbose_name = _("Barrier Plan File")
        verbose_name_plural = _("Barrier Plan Files")


class BarrierRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/barrier/")
    barrier_real = models.ForeignKey(BarrierReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "barrier_real_file"
        verbose_name = _("Barrier Real File")
        verbose_name_plural = _("Barrier Real Files")


auditlog.register(BarrierPlan)
auditlog.register(BarrierReal)
