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
from traffic_control.models.mount import MountPlan, MountReal
from traffic_control.models.plan import Plan


class TrafficLightSoundBeaconValue(Enum):
    NO = 1
    YES = 2

    class Labels:
        NO = _("No")
        YES = _("Yes")


class LocationSpecifier(Enum):
    RIGHT = 1
    ABOVE = 2
    ISLAND = 3

    class Labels:
        RIGHT = _("Right side of the road (relative to traffic direction)")
        ABOVE = _("Above the lanes")
        ISLAND = _("Island")


class TrafficLightType(Enum):
    SIGNAL = "1"
    ARROW_RIGHT = "4.1"
    ARROW_LEFT = "4.2"
    TRIANGLE = "5"
    PUBLIC_TRANSPORT = "8"
    BICYCLE = "9.1"
    BICYCLE_ARROW = "9.2"
    PEDESTRIAN = "10"
    LANE = "11"

    class Labels:
        SIGNAL = _("Traffic signal")
        ARROW_RIGHT = _("Right-turn arrow signal")
        ARROW_LEFT = _("Left-turn arrow signal")
        TRIANGLE = _("Triangle signal")
        PUBLIC_TRANSPORT = _("Public transport signal")
        BICYCLE = _("Bicycle signal")
        BICYCLE_ARROW = _("Bicycle turn arrow signal")
        PEDESTRIAN = _("Pedestrian signal")
        LANE = _("Lane signal")


class VehicleRecognition(Enum):
    LOOP = 1
    INFRARED = 2
    RADAR = 3
    OTHER = 4

    class Labels:
        LOOP = _("Loop sensor")
        INFRARED = _("Infrared sensor")
        RADAR = _("Radar i.e. microwave sensor")
        OTHER = _("Other")


class PushButton(Enum):
    NO = 1
    YES = 2

    class Labels:
        NO = _("No")
        YES = _("Yes")


class AbstractTrafficLight(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    road_name = models.CharField(
        _("Road name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Name of the road this traffic light is installed at."),
    )
    lane_number = EnumField(
        LaneNumber,
        verbose_name=_("Lane number"),
        null=True,
        blank=True,
        help_text=_("Describes which lane of the road this traffic light affects."),
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        null=True,
        blank=True,
        help_text=_("The type of lane which this traffic light affects."),
    )
    direction = models.IntegerField(
        _("Direction"),
        blank=True,
        null=True,
        help_text=_(
            "The direction a person is facing when looking perpendicular to the traffic light. "
            "The value is in degrees from 0 to 359, where 0 is north, 90 is east, etc."
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
        help_text=_("Type of the mount this traffic light is attached to."),
    )
    type = EnumField(
        TrafficLightType,
        blank=True,
        null=True,
        help_text=_("Describes the type of traffic light this device is."),
    )
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.TRAFFIC_LIGHT)),
        help_text=_("Type of the device from Helsinki Design Manual."),
    )
    txt = models.CharField(
        _("Txt"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Text on the traffic light."),
    )
    push_button = EnumIntegerField(
        PushButton,
        verbose_name=_("Push button"),
        blank=True,
        null=True,
        help_text=_("Describes if this traffic light has a push button attached."),
    )
    sound_beacon = EnumIntegerField(
        TrafficLightSoundBeaconValue,
        verbose_name=_("Sound beacon"),
        blank=True,
        null=True,
        help_text=_("Describes if this traffic light has a sound beacon attached."),
    )
    vehicle_recognition = EnumIntegerField(
        VehicleRecognition,
        verbose_name=_("Vehicle recognition"),
        blank=True,
        null=True,
        help_text=_("Describes the type of vehicle recognition this traffic light has."),
    )
    validity_period_start = models.DateField(
        _("Validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this traffic light becomes active."),
    )
    validity_period_end = models.DateField(
        _("Validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this traffic light becomes inactive."),
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        blank=True,
        null=True,
        help_text=_("Specifies where the traffic light is in relation to the road."),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.type} {self.device_type}"

    def save(self, *args, **kwargs):
        if self.device_type and not self.device_type.validate_relation(DeviceTypeTargetModel.TRAFFIC_LIGHT):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic lights')

        super().save(*args, **kwargs)


class TrafficLightPlan(UpdatePlanLocationMixin, AbstractTrafficLight):
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this traffic light is mounted on."),
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="traffic_light_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this traffic light plan is a part of."),
    )

    class Meta:
        db_table = "traffic_light_plan"
        verbose_name = _("Traffic Light Plan")
        verbose_name_plural = _("Traffic Light Plans")
        unique_together = ["source_name", "source_id"]


class TrafficLightReal(AbstractTrafficLight, InstalledDeviceModel):
    traffic_light_plan = models.ForeignKey(
        TrafficLightPlan,
        verbose_name=_("Traffic Light Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this traffic light."),
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this traffic light is mounted on."),
    )

    class Meta:
        db_table = "traffic_light_real"
        verbose_name = _("Traffic Light Real")
        verbose_name_plural = _("Traffic Light Reals")
        unique_together = ["source_name", "source_id"]


class TrafficLightRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"traffic_light": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    traffic_light_real = models.ForeignKey(
        TrafficLightReal,
        verbose_name=_("traffic light real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "traffic_light_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Traffic light real operation")
        verbose_name_plural = _("Traffic light real operations")


class TrafficLightPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/traffic_light/")
    traffic_light_plan = models.ForeignKey(TrafficLightPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "traffic_light_plan_file"
        verbose_name = _("Traffic Light Plan File")
        verbose_name_plural = _("Traffic Light Plan Files")

    def __str__(self):
        return "%s" % self.file


class TrafficLightRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/traffic_light/")
    traffic_light_real = models.ForeignKey(TrafficLightReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "traffic_light_real_file"
        verbose_name = _("Traffic Light Real File")
        verbose_name_plural = _("Traffic Light Real Files")


auditlog.register(TrafficLightPlan)
auditlog.register(TrafficLightReal)
