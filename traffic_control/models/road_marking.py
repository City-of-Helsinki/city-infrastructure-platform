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
    OperationBase,
    OperationType,
    TrafficControlDeviceType,
    TrafficControlDeviceTypeType,
)
from .plan import Plan
from .traffic_sign import TrafficSignPlan, TrafficSignReal
from .utils import SoftDeleteQuerySet


class LineDirection(Enum):
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"

    class Labels:
        FORWARD = _("Forward")
        BACKWARD = _("Backward")


class ArrowDirection(Enum):
    STRAIGHT = 1
    RIGHT = 2
    RIGHT_AND_STRAIGHT = 3
    LEFT = 4
    LEFT_AND_STRAIGHT = 5
    LANE_ENDS = 6
    RIGHT_AND_LEFT = 7
    STRAIGHT_RIGHT_AND_LEFT = 8

    class Labels:
        STRAIGHT = _("Straight")
        RIGHT = _("Right")
        RIGHT_AND_STRAIGHT = _("Right and straight")
        LEFT = _("Left")
        LEFT_AND_STRAIGHT = _("Left and straight")
        LANE_ENDS = _("Lane ends")
        RIGHT_AND_LEFT = _("Right and left")
        STRAIGHT_RIGHT_AND_LEFT = _("Straight, right and left")


class RoadMarkingColor(Enum):
    WHITE = 1
    YELLOW = 2

    class Labels:
        WHITE = _("White")
        YELLOW = _("Yellow")


class LocationSpecifier(Enum):
    BOTH_SIDES_OF_ROAD = 1
    RIGHT_SIDE_OF_LANE = 2
    LEFT_SIDE_OF_LANE = 3
    BOTH_SIDES_OF_LANE = 4
    MIDDLE_OF_LANE = 5
    LEFT_SIDE_OF_LANE_OR_ROAD = 6

    class Labels:
        BOTH_SIDES_OF_ROAD = _("Both sides of road")
        RIGHT_SIDE_OF_LANE = _("Right side of lane")
        LEFT_SIDE_OF_LANE = _("Left side of lane")
        BOTH_SIDES_OF_LANE = _("Both sides of lane ")
        MIDDLE_OF_LANE = _("Middle of lane")
        LEFT_SIDE_OF_LANE_OR_ROAD = _("Left side of lane or road")


class RoadMarkingPlan(
    UpdatePlanLocationMixin, SourceControlModel, SoftDeleteModel, UserControlModel
):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (3D)"), dim=3, srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device Type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.ROAD_MARKING)
        ),
    )
    line_direction = EnumField(
        LineDirection,
        verbose_name=_("Line direction"),
        max_length=10,
        default=LineDirection.FORWARD,
        blank=True,
        null=True,
    )
    arrow_direction = EnumField(
        ArrowDirection,
        verbose_name=_("Arrow direction"),
        max_length=10,
        blank=True,
        null=True,
    )
    value = models.CharField(
        _("Road Marking value"), max_length=254, blank=True, null=True
    )
    size = models.CharField(_("Size"), max_length=254, blank=True, null=True)
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    color = EnumIntegerField(
        RoadMarkingColor,
        verbose_name=_("Color"),
        default=RoadMarkingColor.WHITE,
        blank=True,
        null=True,
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Traffic Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="road_marking_plans",
        blank=True,
        null=True,
    )
    type_specifier = models.CharField(
        _("Type specifier"), max_length=254, blank=True, null=True
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    symbol = models.CharField(_("Symbol"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = EnumField(
        LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT_SIDE_OF_LANE,
        blank=True,
        null=True,
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    width = models.IntegerField(_("Width"), blank=True, null=True)
    is_raised = models.BooleanField(_("Is raised"), null=True)
    is_grinded = models.BooleanField(_("Is grinded"), null=True)
    additional_info = models.TextField(_("Additional info"), blank=True, null=True)
    amount = models.CharField(_("Amount"), max_length=254, blank=True, null=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "road_marking_plan"
        verbose_name = _("Road Marking Plan")
        verbose_name_plural = _("Road Marking Plans")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"{self.id} {self.device_type} {self.value}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.ROAD_MARKING):
            raise ValidationError(
                f'Device type "{self.device_type}" is not allowed for road markings'
            )

        super().save(*args, **kwargs)

        if (
            self.device_type.type == TrafficControlDeviceTypeType.TRANSVERSE
            and self.road_name == ""
        ):
            raise ValidationError(
                f'Road name is required for "{TrafficControlDeviceTypeType.TRANSVERSE.value}" road marking'
            )


class RoadMarkingPlanFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="planfiles/road_marking/"
    )
    road_marking_plan = models.ForeignKey(
        RoadMarkingPlan, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "road_marking_plan_file"
        verbose_name = _("RoadMarking Plan File")
        verbose_name_plural = _("RoadMarking Plan Files")

    def __str__(self):
        return "%s" % self.file


class RoadMarkingReal(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    road_marking_plan = models.ForeignKey(
        RoadMarkingPlan,
        verbose_name=_("Road Marking Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    location = models.GeometryField(_("Location (3D)"), dim=3, srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            Q(target_model=None) | Q(target_model=DeviceTypeTargetModel.ROAD_MARKING)
        ),
    )
    line_direction = EnumField(
        LineDirection,
        verbose_name=_("Line direction"),
        max_length=10,
        default=LineDirection.FORWARD,
        blank=True,
        null=True,
    )
    arrow_direction = EnumField(
        ArrowDirection,
        verbose_name=_("Arrow direction"),
        max_length=10,
        blank=True,
        null=True,
    )
    value = models.CharField(
        _("Road Marking value"), max_length=254, blank=True, null=True
    )
    size = models.CharField(_("Size"), max_length=254, blank=True, null=True)
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    color = EnumIntegerField(
        RoadMarkingColor,
        verbose_name=_("Color"),
        default=RoadMarkingColor.WHITE,
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
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    traffic_sign_real = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("Traffic Sign Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    missing_traffic_sign_real_txt = models.CharField(
        _("Missing Traffic Sign Real txt"), max_length=254, blank=True, null=True
    )
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        default=Condition.VERY_GOOD,
        blank=True,
        null=True,
    )
    type_specifier = models.CharField(
        _("Type specifier"), max_length=254, blank=True, null=True
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    symbol = models.CharField(_("Symbol"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = EnumField(
        LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True
    )
    lane_type = EnumField(
        LaneType,
        verbose_name=_("Lane type"),
        default=LaneType.MAIN,
        blank=True,
    )
    location_specifier = EnumIntegerField(
        LocationSpecifier,
        verbose_name=_("Location specifier"),
        default=LocationSpecifier.RIGHT_SIDE_OF_LANE,
        blank=True,
        null=True,
    )
    length = models.IntegerField(_("Length"), blank=True, null=True)
    width = models.IntegerField(_("Width"), blank=True, null=True)
    is_raised = models.BooleanField(_("Is raised"), null=True)
    is_grinded = models.BooleanField(_("Is grinded"), null=True)
    additional_info = models.TextField(_("Additional info"), blank=True, null=True)
    amount = models.CharField(_("Amount"), max_length=254, blank=True, null=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "road_marking_real"
        verbose_name = _("Road Marking Real")
        verbose_name_plural = _("Road Marking Reals")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return f"{self.id} {self.device_type} {self.value}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(DeviceTypeTargetModel.ROAD_MARKING):
            raise ValidationError(
                f'Device type "{self.device_type}" is not allowed for road markings'
            )

        if (
            self.device_type.type == TrafficControlDeviceTypeType.TRANSVERSE
            and self.road_name == ""
        ):
            raise ValidationError(
                f'Road name is required for "{TrafficControlDeviceTypeType.TRANSVERSE.value}" road marking'
            )

        super().save(*args, **kwargs)


class RoadMarkingRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"road_marking": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    road_marking_real = models.ForeignKey(
        RoadMarkingReal,
        verbose_name=_("road marking real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "road_marking_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Road marking real operation")
        verbose_name_plural = _("Road marking real operations")


class RoadMarkingRealFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="realfiles/road_marking/"
    )
    road_marking_real = models.ForeignKey(
        RoadMarkingReal, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "road_marking_real_file"
        verbose_name = _("RoadMarking Real File")
        verbose_name_plural = _("RoadMarking Real Files")

    def __str__(self):
        return f"{self.file}"


auditlog.register(RoadMarkingPlan)
auditlog.register(RoadMarkingReal)
