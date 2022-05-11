from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.enums import DeviceTypeTargetModel, LaneNumber, LaneType, Reflection, Size
from traffic_control.mixins.models import (
    AbstractFileModel,
    DecimalValueFromDeviceTypeMixin,
    InstalledDeviceModel,
    OwnedDeviceModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.common import OperationBase, OperationType, TrafficControlDeviceType
from traffic_control.models.mount import MountPlan, MountReal
from traffic_control.models.plan import Plan


class LocationSpecifier(Enum):
    RIGHT = 1
    LEFT = 2
    ABOVE = 3
    MIDDLE = 4
    VERTICAL = 5

    class Labels:
        RIGHT = _("Right side")
        LEFT = _("Left side")
        ABOVE = _("Above")
        MIDDLE = _("Middle")
        VERTICAL = _("Vertical")


class AbstractSignpost(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
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
        default=LaneNumber.MAIN_1,
        blank=True,
        help_text=_("Describes which lane of the road this sign affects."),
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
        help_text=_("The type of lane which this sign affects."),
    )
    direction = models.IntegerField(
        _("Direction"),
        default=0,
        help_text=_(
            "Direction of the device in degrees. "
            "If 'road name' is entered the direction is in relation to the road. Otherwise cardinal direction is used. "
            "e.g. 0 = North, 45 = North East, 90 = East, 180 = South."
        ),
    )
    height = models.DecimalField(
        _("Height"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("The height of the sign from the ground, measured from the top in centimeters."),
    )
    mount_type = models.ForeignKey(
        "MountType",
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Type of the mount this sign is attached to."),
    )
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.SIGNPOST)),
        help_text=_("Type of the device from Helsinki Design Manual."),
    )
    value = models.DecimalField(
        _("Signpost value"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Numeric value on the sign."),
    )
    txt = models.CharField(
        _("Signpost txt"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Text written on the device."),
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
    attachment_class = models.CharField(
        _("Attachment class"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_(
            "The attachment class of the sign according to the standard SFS-EN 12899-1."
            "The possible values are P1, P2 and P3."
        ),
    )
    target_id = models.CharField(
        _("Target ID"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("The id number of the target the sign is guiding to (if available)."),
    )
    target_txt = models.CharField(
        _("Target txt"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Free-form text description of the target the sign is guiding to, if the target has no id number."),
    )
    electric_maintainer = models.CharField(
        _("Electric maintainer"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Organization in charge of electric maintenance of the device."),
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
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
        return f"{self.id} {self.device_type} {self.txt}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.SIGNPOST):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for signposts')

        super().save(*args, **kwargs)


class SignpostPlan(DecimalValueFromDeviceTypeMixin, UpdatePlanLocationMixin, AbstractSignpost):
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this sign is mounted on."),
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Signpost inside which this device is located."),
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="signpost_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this signpost plan is a part of."),
    )

    class Meta:
        db_table = "signpost_plan"
        verbose_name = _("Signpost Plan")
        verbose_name_plural = _("Signpost Plans")
        unique_together = ["source_name", "source_id"]


class SignpostReal(DecimalValueFromDeviceTypeMixin, AbstractSignpost, InstalledDeviceModel):
    signpost_plan = models.ForeignKey(
        SignpostPlan,
        verbose_name=_("Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this signpost."),
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Signpost Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Signpost inside which this device is located."),
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this sign is mounted on."),
    )
    material = models.CharField(
        _("Material"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Describes the material that the device is made of."),
    )
    organization = models.CharField(
        _("Organization"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("The organization that installed the signpost."),
    )
    manufacturer = models.CharField(
        _("Manufacturer"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the organization that manufactured this device."),
    )

    class Meta:
        db_table = "signpost_real"
        verbose_name = _("Signpost Real")
        verbose_name_plural = _("Signpost Reals")
        unique_together = ["source_name", "source_id"]


class SignpostRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"signpost": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    signpost_real = models.ForeignKey(
        SignpostReal,
        verbose_name=_("signpost real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "signpost_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Signpost real operation")
        verbose_name_plural = _("Signpost real operations")


class SignpostPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/signpost/")
    signpost_plan = models.ForeignKey(SignpostPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "signpost_plan_file"
        verbose_name = _("Signpost Plan File")
        verbose_name_plural = _("Signpost Plan Files")


class SignpostRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/signpost/")
    signpost_real = models.ForeignKey(SignpostReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "signpost_real_file"
        verbose_name = _("Signpost Real File")
        verbose_name_plural = _("Signpost Real Files")


auditlog.register(SignpostPlan)
auditlog.register(SignpostReal)
