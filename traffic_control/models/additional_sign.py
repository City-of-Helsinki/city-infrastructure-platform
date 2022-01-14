import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.enums import (
    Condition,
    DeviceTypeTargetModel,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    Reflection,
    Size,
    Surface,
)
from traffic_control.mixins.models import SoftDeleteModel, SourceControlModel, UpdatePlanLocationMixin, UserControlModel
from traffic_control.models.affect_area import CoverageArea
from traffic_control.models.common import OperationBase, OperationType, TrafficControlDeviceType
from traffic_control.models.mount import MountPlan, MountReal, MountType
from traffic_control.models.plan import Plan
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignPlan, TrafficSignReal
from traffic_control.models.utils import SoftDeleteQuerySet


class Color(Enum):
    BLUE = 1
    YELLOW = 2

    class Labels:
        BLUE = _("Blue")
        YELLOW = _("Yellow")


class AbstractAdditionalSign(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    height = models.IntegerField(_("Height"), blank=True, null=True)
    direction = models.IntegerField(_("Direction"), default=0)
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
    color = EnumIntegerField(Color, verbose_name=_("Color"), default=Color.BLUE, blank=True, null=True)
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
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

    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )

    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)
    seasonal_validity_period_start = models.DateField(_("Seasonal validity period start"), blank=True, null=True)
    seasonal_validity_period_end = models.DateField(_("Seasonal validity period end"), blank=True, null=True)
    lifecycle = EnumIntegerField(Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} {self.id}"


class AdditionalSignPlan(UpdatePlanLocationMixin, AbstractAdditionalSign):
    parent = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Parent Traffic Sign Plan"),
        on_delete=models.PROTECT,
        related_name="additional_signs",
        blank=True,
        null=True,
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="additional_sign_plans",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "additional_sign_plan"
        verbose_name = _("Additional Sign Plan")
        verbose_name_plural = _("Additional Sign Plans")
        unique_together = ["source_name", "source_id"]


class AdditionalSignReal(AbstractAdditionalSign):
    parent = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("Parent Traffic Sign Real"),
        on_delete=models.PROTECT,
        related_name="additional_signs",
        blank=True,
        null=True,
    )
    additional_sign_plan = models.ForeignKey(
        AdditionalSignPlan,
        verbose_name=_("Additional Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
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
    installation_id = models.CharField(_("Installation id"), max_length=254, blank=True, null=True)
    installation_details = models.CharField(_("Installation details"), max_length=254, blank=True, null=True)
    installation_date = models.DateField(_("Installation date"), blank=True, null=True)
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        default=InstallationStatus.IN_USE,
        blank=True,
        null=True,
    )
    installed_by = models.CharField(_("Installed by"), max_length=256, blank=True)
    manufacturer = models.CharField(_("Manufacturer"), max_length=254, blank=True, null=True)
    rfid = models.CharField(_("RFID"), max_length=254, blank=True, null=True)
    legacy_code = models.CharField(_("Legacy Traffic Sign Code"), max_length=32, blank=True, null=True)
    permit_decision_id = models.CharField(_("Permit decision id"), max_length=254, blank=True, null=True)
    operation = models.CharField(_("Operation"), max_length=64, blank=True, null=True)
    scanned_at = models.DateTimeField(_("Scanned at"), blank=True, null=True)
    size = EnumField(
        Size,
        verbose_name=_("Size"),
        max_length=1,
        blank=True,
        null=True,
    )
    attachment_url = models.URLField(_("Attachment url"), max_length=500, blank=True, null=True)
    coverage_area = models.ForeignKey(
        CoverageArea,
        verbose_name=_("Coverage area"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        db_table = "additional_sign_real"
        verbose_name = _("Additional Sign Real")
        verbose_name_plural = _("Additional Sign Reals")
        unique_together = ["source_name", "source_id"]


class AdditionalSignRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"additional_sign": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    additional_sign_real = models.ForeignKey(
        AdditionalSignReal,
        verbose_name=_("additional sign real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "additional_sign_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Additional sign real operation")
        verbose_name_plural = _("Additional sign real operations")


class AbstractAdditionalSignContent(SourceControlModel, UserControlModel):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)

    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)),
        null=True,
        blank=False,
    )
    text = models.CharField(verbose_name=_("Content text"), max_length=256, blank=True)
    order = models.SmallIntegerField(verbose_name=_("Order"), default=1, blank=False, null=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.__class__.__name__} at position {self.order} for {self.parent}"

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.ADDITIONAL_SIGN):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic signs')

        if not self.device_type:
            self.device_type = (
                TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.ADDITIONAL_SIGN)
                .filter(legacy_code=self.parent.legacy_code)
                .order_by("code")
                .first()
            )

        super().save(*args, **kwargs)


class AdditionalSignContentPlan(AbstractAdditionalSignContent):
    parent = models.ForeignKey(
        AdditionalSignPlan,
        verbose_name=_("Parent Additional Sign Plan"),
        on_delete=models.CASCADE,
        related_name="content",
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = _("Additional Sign Content Plan")
        verbose_name_plural = _("Additional Sign Content Plans")
        ordering = ("parent", "order")


class AdditionalSignContentReal(AbstractAdditionalSignContent):
    parent = models.ForeignKey(
        AdditionalSignReal,
        verbose_name=_("Parent Additional Sign Real"),
        on_delete=models.CASCADE,
        related_name="content",
        blank=False,
        null=False,
    )

    class Meta:
        verbose_name = _("Additional Sign Content Real")
        verbose_name_plural = _("Additional Sign Content Reals")
        ordering = ("parent", "order")


auditlog.register(AdditionalSignPlan)
auditlog.register(AdditionalSignReal)
auditlog.register(AdditionalSignContentPlan)
auditlog.register(AdditionalSignContentReal)
