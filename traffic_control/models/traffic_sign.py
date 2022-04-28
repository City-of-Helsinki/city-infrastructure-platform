import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
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
from traffic_control.mixins.models import (
    AbstractFileModel,
    DecimalValueFromDeviceTypeMixin,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.affect_area import CoverageArea
from traffic_control.models.common import OperationBase, OperationType, TrafficControlDeviceType
from traffic_control.models.mount import MountPlan, MountReal
from traffic_control.models.plan import Plan
from traffic_control.models.utils import SoftDeleteQuerySet


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


class TrafficSignPlanQuerySet(SoftDeleteQuerySet):
    def soft_delete(self, user):
        from traffic_control.models.additional_sign import AdditionalSignPlan

        additional_signs = AdditionalSignPlan.objects.filter(parent__in=self).active()

        super().soft_delete(user)
        additional_signs.soft_delete(user)


class TrafficSignRealQuerySet(SoftDeleteQuerySet):
    def soft_delete(self, user):
        from traffic_control.models.additional_sign import AdditionalSignReal

        additional_signs = AdditionalSignReal.objects.filter(parent__in=self).active()

        super().soft_delete(user)
        additional_signs.soft_delete(user)


class AbstractTrafficSign(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = EnumField(LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True)
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
    )
    direction = models.IntegerField(_("Direction"), default=0)
    height = models.IntegerField(_("Height"), blank=True, null=True)
    mount_type = models.ForeignKey(
        "MountType",
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    value = models.DecimalField(
        _("Traffic Sign Code value"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    lifecycle = EnumIntegerField(Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE)
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)
    seasonal_validity_period_start = models.DateField(_("Seasonal validity period start"), blank=True, null=True)
    seasonal_validity_period_end = models.DateField(_("Seasonal validity period end"), blank=True, null=True)
    responsible_entity = models.ForeignKey(
        "traffic_control.ResponsibleEntity",
        verbose_name=_("Responsible entity"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def has_additional_signs(self):
        return self.additional_signs.active().exists()

    @transaction.atomic
    def soft_delete(self, user):
        super().soft_delete(user)
        self.additional_signs.soft_delete(user)


class TrafficSignPlan(DecimalValueFromDeviceTypeMixin, UpdatePlanLocationMixin, AbstractTrafficSign):
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)),
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    affect_area = models.PolygonField(_("Affect area (2D)"), srid=settings.SRID, blank=True, null=True)
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="traffic_sign_plans",
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

    objects = TrafficSignPlanQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_plan"
        verbose_name = _("Traffic Sign Plan")
        verbose_name_plural = _("Traffic Sign Plans")
        unique_together = ["source_name", "source_id"]

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.TRAFFIC_SIGN):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic signs')

        super().save(*args, **kwargs)


class TrafficSignReal(DecimalValueFromDeviceTypeMixin, AbstractTrafficSign):
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Traffic Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)),
        blank=False,
        null=True,
    )
    legacy_code = models.CharField(_("Legacy Traffic Sign Code"), max_length=32, blank=True, null=True)
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    installation_id = models.CharField(_("Installation id"), max_length=254, blank=True, null=True)
    installation_details = models.CharField(_("Installation details"), max_length=254, blank=True, null=True)
    permit_decision_id = models.CharField(_("Permit decision id"), max_length=254, blank=True, null=True)
    coverage_area = models.ForeignKey(
        CoverageArea,
        verbose_name=_("Coverage area"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    scanned_at = models.DateTimeField(_("Scanned at"), blank=True, null=True)
    size = EnumField(
        Size,
        verbose_name=_("Size"),
        max_length=1,
        blank=True,
        null=True,
    )
    reflection_class = EnumField(
        Reflection,
        verbose_name=_("Reflection"),
        max_length=2,
        blank=True,
        null=True,
    )
    surface_class = EnumField(
        Surface,
        verbose_name=_("Surface"),
        max_length=6,
        blank=True,
        null=True,
    )
    manufacturer = models.CharField(_("Manufacturer"), max_length=254, blank=True, null=True)
    rfid = models.CharField(_("RFID"), max_length=254, blank=True, null=True)
    operation = models.CharField(_("Operation"), max_length=64, blank=True, null=True)
    attachment_url = models.URLField(_("Attachment url"), max_length=500, blank=True, null=True)
    installation_date = models.DateField(_("Installation date"), blank=True, null=True)
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        blank=True,
        null=True,
    )
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        blank=True,
        null=True,
    )

    objects = TrafficSignRealQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")
        unique_together = ["source_name", "source_id"]

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.TRAFFIC_SIGN):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic signs')

        if not self.device_type:
            self.device_type = (
                TrafficControlDeviceType.objects.for_target_model(DeviceTypeTargetModel.TRAFFIC_SIGN)
                .filter(legacy_code=self.legacy_code)
                .order_by("code")
                .first()
            )

        super().save(*args, **kwargs)


class TrafficSignRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"traffic_sign": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    traffic_sign_real = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("traffic sign real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "traffic_sign_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Traffic sign real operation")
        verbose_name_plural = _("Traffic sign real operations")


class TrafficSignPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/traffic_sign/")
    traffic_sign_plan = models.ForeignKey(TrafficSignPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "traffic_sign_plan_file"
        verbose_name = _("Traffic Sign Plan File")
        verbose_name_plural = _("Traffic Sign Plan Files")


class TrafficSignRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/traffic_sign/")
    traffic_sign_real = models.ForeignKey(TrafficSignReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "traffic_sign_real_file"
        verbose_name = _("Traffic Sign Real File")
        verbose_name_plural = _("Traffic Sign Real Files")


auditlog.register(TrafficSignPlan)
auditlog.register(TrafficSignReal)
