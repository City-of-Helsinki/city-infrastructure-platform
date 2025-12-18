from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from traffic_control.enums import DeviceTypeTargetModel, LaneNumber, LaneType
from traffic_control.mixins.models import (
    AbstractFileModel,
    BoundaryCheckedLocationMixin,
    InstalledDeviceModel,
    OwnedDeviceModel,
    ReplaceableDevicePlanMixin,
    REPLACEMENT_TO_NEW,
    REPLACEMENT_TO_OLD,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
    UUIDModel,
)
from traffic_control.models.common import (
    OperationBase,
    OperationType,
    TrafficControlDeviceType,
    VERBOSE_NAME_NEW,
    VERBOSE_NAME_OLD,
)
from traffic_control.models.plan import Plan


class ConnectionType(models.IntegerChoices):
    CLOSED = 1, _("Closed")
    OPEN_OUT = 2, _("Open out")


class Reflective(models.TextChoices):
    YES = "YES", _("Yes")
    NO = "NO", _("No")
    RED_YELLOW = "RED_YELLOW", _("Red-yellow")


class LocationSpecifier(models.IntegerChoices):
    MIDDLE = 1, _("Middle of road or lane")
    RIGHT = 2, _("Right of road or lane")
    LEFT = 3, _("Left of road or lane")


class AbstractBarrier(
    BoundaryCheckedLocationMixin, SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel, UUIDModel
):
    location = models.GeometryField(_("Location (3D)"), dim=3, srid=settings.SRID)
    road_name = models.CharField(
        _("Road name"),
        max_length=254,
        help_text=_("Name of the road this barrier is installed at."),
    )
    lane_number = EnumField(
        LaneNumber,
        verbose_name=_("Lane number"),
        null=True,
        blank=True,
        help_text=_("Describes which lane of the road this barrier affects."),
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        null=True,
        blank=True,
        help_text=_("The type of lane which this barrier affects."),
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        blank=True,
        null=True,
        help_text=_("Specifies where the barrier is in relation to the road."),
    )
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.BARRIER)),
        help_text=_("Type of the device from Helsinki Design Manual."),
    )
    connection_type = EnumIntegerField(
        ConnectionType,
        verbose_name=_("Connection type"),
        default=ConnectionType.CLOSED,
        help_text=_("Describes if the barrier is open or closed."),
    )
    material = models.CharField(
        _("Material"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Describes the material that the barrier is made of."),
    )
    is_electric = models.BooleanField(
        _("Is electric"),
        default=False,
    )
    reflective = EnumField(
        Reflective,
        verbose_name=_("Reflective"),
        blank=True,
        null=True,
    )
    validity_period_start = models.DateField(
        _("Validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this barrier becomes active."),
    )
    validity_period_end = models.DateField(
        _("Validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this barrier becomes inactive."),
    )
    length = models.IntegerField(
        _("Length"),
        blank=True,
        null=True,
        help_text=_("Length of the barrier in centimeters."),
    )
    count = models.IntegerField(
        _("Count"),
        blank=True,
        null=True,
    )
    txt = models.TextField(
        _("Txt"),
        blank=True,
        null=True,
        help_text=_("Text written on the barrier."),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.BARRIER):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for barriers')

        super().save(*args, **kwargs)


class BarrierPlan(UpdatePlanLocationMixin, ReplaceableDevicePlanMixin, AbstractBarrier):
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="barrier_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this Barrier Plan is a part of."),
    )

    class Meta:
        db_table = "barrier_plan"
        verbose_name = _("Barrier Plan")
        verbose_name_plural = _("Barrier Plans")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
        ]


class BarrierPlanReplacement(models.Model):
    id = models.BigAutoField(primary_key=True)
    new = models.OneToOneField(
        BarrierPlan,
        verbose_name=VERBOSE_NAME_NEW,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_OLD,
    )
    old = models.OneToOneField(
        BarrierPlan,
        verbose_name=VERBOSE_NAME_OLD,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_NEW,
    )

    class Meta:
        db_table = "barrier_plan_replacement"
        verbose_name = _("Barrier Plan Replacement")
        verbose_name_plural = _("Barrier Plan Replacements")


class BarrierReal(AbstractBarrier, InstalledDeviceModel):
    barrier_plan = models.ForeignKey(
        BarrierPlan,
        verbose_name=_("Barrier Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this barrier."),
    )

    class Meta:
        db_table = "barrier_real"
        verbose_name = _("Barrier real")
        verbose_name_plural = _("Barrier reals")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
            models.UniqueConstraint(
                fields=["barrier_plan"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_barrier_plan_id",
            ),
        ]


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
