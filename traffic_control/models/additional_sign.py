from enum import member

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.enums import DeviceTypeTargetModel, LaneNumber, LaneType, Reflection, Size, Surface
from traffic_control.mixins.models import (
    AbstractFileModel,
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
from traffic_control.models.mount import MountPlan, MountReal, MountType
from traffic_control.models.plan import Plan
from traffic_control.models.traffic_sign import LocationSpecifier, TrafficSignPlan, TrafficSignReal
from traffic_control.validators import validate_structured_content


class Color(Enum):
    BLUE = 1
    YELLOW = 2

    @member
    class Labels:
        BLUE = _("Blue")
        YELLOW = _("Yellow")


class AbstractAdditionalSign(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)),
    )
    order = models.SmallIntegerField(
        verbose_name=_("Order"),
        default=1,
        blank=False,
        null=False,
        help_text=_(
            "The order of the sign in relation to the signs at the same point. "
            "Order from top to bottom, from left to right starting at 1."
        ),
    )
    content_s = models.JSONField(
        verbose_name=_("Content"),
        blank=True,
        null=True,
        help_text=_("Additional sign content as JSON document"),
    )
    missing_content = models.BooleanField(
        _("Missing content"),
        default=False,
        help_text=_("Content (content_s) is not available although the device type content schema requires it."),
    )
    additional_information = models.TextField(
        _("Additional information"),
        blank=True,
        null=False,
        default="",
        help_text=_("Additional information related to this device."),
    )
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    height = models.IntegerField(
        _("Height"),
        blank=True,
        null=True,
        help_text=_("The height of the sign from the ground, measured from the bottom in centimeters."),
    )
    size = EnumField(
        Size,
        verbose_name=_("Size"),
        max_length=1,
        blank=True,
        null=True,
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
    color = EnumIntegerField(
        Color,
        verbose_name=_("Color"),
        blank=True,
        null=True,
    )
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Type of the mount this sign is attached to."),
    )
    road_name = models.CharField(
        _("Road name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the road this sign is installed at."),
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

    def clean(self):
        validation_errors = {}

        if self.missing_content and self.content_s:
            validation_errors["missing_content"] = ValidationError(
                _("'Missing content' cannot be enabled when the content field (content_s) is not empty.")
            )

        if not self.missing_content:
            content_s_validation_errors = validate_structured_content(self.content_s, self.device_type)
            if len(content_s_validation_errors) > 0:
                validation_errors["content_s"] = content_s_validation_errors

        if len(validation_errors) > 0:
            raise ValidationError(validation_errors)

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.ADDITIONAL_SIGN):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for additional signs')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__} {self.id}"


class AdditionalSignPlan(UpdatePlanLocationMixin, ReplaceableDevicePlanMixin, AbstractAdditionalSign):
    parent = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Parent Traffic Sign Plan"),
        on_delete=models.PROTECT,
        related_name="additional_signs",
        blank=True,
        null=True,
        help_text=_("The traffic sign to which this additional sign is associated."),
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this sign is mounted on."),
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="additional_sign_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this Additional Sign Plan is a part of."),
    )

    class Meta:
        db_table = "additional_sign_plan"
        verbose_name = _("Additional Sign Plan")
        verbose_name_plural = _("Additional Sign Plans")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
        ]


class AdditionalSignPlanReplacement(models.Model):
    id = models.BigAutoField(primary_key=True)
    new = models.OneToOneField(
        AdditionalSignPlan,
        verbose_name=VERBOSE_NAME_NEW,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_OLD,
    )
    old = models.OneToOneField(
        AdditionalSignPlan,
        verbose_name=VERBOSE_NAME_OLD,
        unique=True,
        on_delete=models.CASCADE,
        related_name=REPLACEMENT_TO_NEW,
    )

    class Meta:
        db_table = "additional_sign_plan_replacement"
        verbose_name = _("Additional Sign Plan Replacement")
        verbose_name_plural = _("Additional Sign Plan Replacements")


class AdditionalSignReal(AbstractAdditionalSign, InstalledDeviceModel):
    parent = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("Parent Traffic Sign Real"),
        on_delete=models.PROTECT,
        related_name="additional_signs",
        blank=True,
        null=True,
        help_text=_("The traffic sign to which this additional sign is associated."),
    )
    additional_sign_plan = models.ForeignKey(
        AdditionalSignPlan,
        verbose_name=_("Additional Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this Additional Sign."),
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
    installed_by = models.CharField(
        _("Installed by"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the organization who installed this sign."),
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
    legacy_code = models.CharField(
        _("Legacy Traffic Sign Code"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("The sign type code of the sign in the old Finnish road traffic law."),
    )
    permit_decision_id = models.CharField(
        _("Permit decision id"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("The id number of the installation permit."),
    )
    operation = models.CharField(
        _("Operation"),
        max_length=64,
        blank=True,
        null=True,
        help_text=_("Maintenance operations done to the sign, e.g. washing, straightening or painting."),
    )
    scanned_at = models.DateTimeField(
        _("Scanned at"),
        blank=True,
        null=True,
        help_text=_("Date and time on which this sign was last scanned at."),
    )
    attachment_url = models.URLField(
        _("Attachment url"),
        max_length=500,
        blank=True,
        null=True,
        help_text=_("URL to a file attachment related to this sign."),
    )
    coverage_area = models.ForeignKey(
        CoverageArea,
        verbose_name=_("Coverage area"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text=_("Coverage area that this sign belongs to."),
    )

    class Meta:
        db_table = "additional_sign_real"
        verbose_name = _("Additional Sign Real")
        verbose_name_plural = _("Additional Sign Reals")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
            models.UniqueConstraint(
                fields=["additional_sign_plan"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_additional_sign_plan_id",
            ),
        ]


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


class AdditionalSignPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/additional_sign/")
    additional_sign_plan = models.ForeignKey(AdditionalSignPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "additional_sign_plan_file"
        verbose_name = _("Additional Sign Plan File")
        verbose_name_plural = _("Additional Sign Plan Files")


class AdditionalSignRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/additional_sign/")
    additional_sign_real = models.ForeignKey(AdditionalSignReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "additional_sign_real_file"
        verbose_name = _("Additional Sign Real File")
        verbose_name_plural = _("Additional Sign Real Files")


auditlog.register(AdditionalSignPlan)
auditlog.register(AdditionalSignPlanFile)
auditlog.register(AdditionalSignReal)
auditlog.register(AdditionalSignRealFile)
auditlog.register(AdditionalSignPlanReplacement)
