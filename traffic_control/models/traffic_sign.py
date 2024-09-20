from enum import member

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.enums import DeviceTypeTargetModel, LaneNumber, LaneType, Reflection, Size, Surface
from traffic_control.mixins.models import (
    AbstractFileModel,
    DecimalValueFromDeviceTypeMixin,
    InstalledDeviceModel,
    OwnedDeviceModel,
    ReplaceableDevicePlanMixin,
    REPLACEMENT_TO_NEW,
    REPLACEMENT_TO_OLD,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.affect_area import CoverageArea
from traffic_control.models.common import (
    OperationBase,
    OperationType,
    TrafficControlDeviceType,
    VERBOSE_NAME_NEW,
    VERBOSE_NAME_OLD,
)
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

    @member
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


class AbstractTrafficSign(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)),
        help_text=_("Type of the device from Helsinki Design Manual."),
    )
    road_name = models.CharField(
        _("Road name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the road this traffic sign is installed at."),
    )
    lane_number = EnumField(
        LaneNumber,
        verbose_name=_("Lane number"),
        null=True,
        blank=True,
        help_text=_("Describes which lane of the road this sign affects."),
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        null=True,
        blank=True,
        help_text=_("The type of lane which this sign affects."),
    )
    direction = models.IntegerField(
        _("Direction"),
        blank=True,
        null=True,
        help_text=_(
            "The direction a person is facing when looking perpendicular to the sign. "
            "The value is in degrees from 0 to 359, where 0 is north, 90 is east, etc."
        ),
    )
    height = models.IntegerField(
        _("Height"),
        blank=True,
        null=True,
        help_text=_("The height of the sign from the ground, measured from the bottom in centimeters."),
    )
    mount_type = models.ForeignKey(
        "MountType",
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Type of the mount this sign is attached to."),
    )
    value = models.DecimalField(
        _("Traffic Sign Code value"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Numeric value on the sign."),
    )
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
    txt = models.CharField(
        _("Txt"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Text written on the sign."),
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        blank=True,
        null=True,
        help_text=_("Specifies where the sign is in relation to the road."),
    )
    validity_period_start = models.DateField(
        _("Validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this sign becomes active."),
    )
    validity_period_end = models.DateField(
        _("Validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this sign becomes inactive."),
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this sign becomes seasonally active."),
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this sign becomes seasonally inactive."),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def has_additional_signs(self):
        return self.additional_signs.active().exists()

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.TRAFFIC_SIGN):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic signs')

        super().save(*args, **kwargs)

    @transaction.atomic
    def soft_delete(self, user):
        super().soft_delete(user)
        self.additional_signs.soft_delete(user)


class TrafficSignPlan(
    DecimalValueFromDeviceTypeMixin,
    UpdatePlanLocationMixin,
    ReplaceableDevicePlanMixin,
    AbstractTrafficSign,
):
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this sign is mounted on."),
    )
    affect_area = models.PolygonField(_("Affect area (2D)"), srid=settings.SRID, blank=True, null=True)
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="traffic_sign_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this traffic sign plan is a part of."),
    )

    objects = TrafficSignPlanQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_plan"
        verbose_name = _("Traffic Sign Plan")
        verbose_name_plural = _("Traffic Sign Plans")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
        ]


class TrafficSignPlanReplacement(models.Model):
    id = models.BigAutoField(primary_key=True)
    new = models.OneToOneField(
        TrafficSignPlan,
        verbose_name=VERBOSE_NAME_NEW,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_OLD,
    )
    old = models.OneToOneField(
        TrafficSignPlan,
        verbose_name=VERBOSE_NAME_OLD,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_NEW,
    )

    class Meta:
        db_table = "traffic_sign_plan_replacement"
        verbose_name = _("Traffic Sign Plan Replacement")
        verbose_name_plural = _("Traffic Sign Plan Replacements")


class TrafficSignReal(DecimalValueFromDeviceTypeMixin, AbstractTrafficSign, InstalledDeviceModel):
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Traffic Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this traffic sign."),
    )
    legacy_code = models.CharField(
        _("Legacy Traffic Sign Code"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("The device type code of the sign in the old Finnish road traffic law."),
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this sign is mounted on."),
    )
    installation_id = models.CharField(
        _("Installation id"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("The id number of the installation record."),
    )
    installation_details = models.CharField(
        _("Installation details"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Additional details about the installation."),
    )
    permit_decision_id = models.CharField(
        _("Permit decision id"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("The id number of the installation permit."),
    )
    coverage_area = models.ForeignKey(
        CoverageArea,
        verbose_name=_("Coverage area"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text=_("Coverage area that this traffic sign belongs to."),
    )
    scanned_at = models.DateTimeField(
        _("Scanned at"),
        blank=True,
        null=True,
        help_text=_("Date and time on which this sign was last scanned at."),
    )
    manufacturer = models.CharField(
        _("Manufacturer"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the organization that manufactured this sign."),
    )
    rfid = models.CharField(
        _("RFID"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("RFID tag of the sign (if any)."),
    )
    operation = models.CharField(
        _("Operation"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("Maintenance operations done to the sign, e.g. washing, straightening or painting."),
    )
    attachment_url = models.URLField(
        _("Attachment url"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL to a file attachment related to this sign."),
    )

    objects = TrafficSignRealQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
        ]


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
auditlog.register(TrafficSignPlanFile)
auditlog.register(TrafficSignReal)
auditlog.register(TrafficSignRealFile)
