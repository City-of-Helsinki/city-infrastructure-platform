import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from traffic_control.mixins.models import (
    AbstractFileModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.common import (
    Condition,
    DeviceTypeTargetModel,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    OperationBase,
    OperationType,
    TrafficControlDeviceType,
)
from traffic_control.models.mount import MountPlan, MountReal
from traffic_control.models.plan import Plan
from traffic_control.models.utils import SoftDeleteQuerySet


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


class AbstractTrafficLight(SourceControlModel, SoftDeleteModel, UserControlModel):
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
    height = models.DecimalField(_("Height"), max_digits=5, decimal_places=2, blank=True, null=True)
    mount_type = models.ForeignKey(
        "MountType",
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    type = EnumField(TrafficLightType, blank=True, null=True)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.TRAFFIC_LIGHT)),
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE)
    push_button = EnumIntegerField(
        PushButton,
        verbose_name=_("Push button"),
        blank=True,
        null=True,
    )
    sound_beacon = EnumIntegerField(
        TrafficLightSoundBeaconValue,
        verbose_name=_("Sound beacon"),
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
    vehicle_recognition = EnumIntegerField(
        VehicleRecognition,
        verbose_name=_("Vehicle recognition"),
        blank=True,
        null=True,
    )
    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.type} {self.device_type}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.TRAFFIC_LIGHT):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for traffic lights')

        super().save(*args, **kwargs)


class TrafficLightPlan(UpdatePlanLocationMixin, AbstractTrafficLight):
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
        related_name="traffic_light_plans",
        blank=True,
        null=True,
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "traffic_light_plan"
        verbose_name = _("Traffic Light Plan")
        verbose_name_plural = _("Traffic Light Plans")
        unique_together = ["source_name", "source_id"]


class TrafficLightReal(AbstractTrafficLight):
    traffic_light_plan = models.ForeignKey(
        TrafficLightPlan,
        verbose_name=_("Traffic Light Plan"),
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
    installation_date = models.DateField(_("Installation date"), blank=True, null=True)
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        default=InstallationStatus.IN_USE,
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

    objects = SoftDeleteQuerySet.as_manager()

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
