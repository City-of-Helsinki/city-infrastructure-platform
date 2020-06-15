import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from ..mixins.models import SoftDeleteModel, UserControlModel
from .common import (
    Condition,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    TrafficControlDeviceType,
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
    RIGHT_AND_STRAIGHT = 2
    LEFT = 4
    LEFT_AND_STRAIGHT = 5

    class Labels:
        STRAIGHT = _("Straight")
        RIGHT = _("Right")
        RIGHT_AND_STRAIGHT = _("Right and straight")
        LEFT = _("Left")
        LEFT_AND_STRAIGHT = _("Left and straight")


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


class RoadMarkingPlan(SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device Type"),
        on_delete=models.PROTECT,
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
    decision_date = models.DateField(_("Decision date"))
    decision_id = models.CharField(
        _("Decision id"), max_length=254, blank=True, null=True
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
    has_rumble_strips = models.BooleanField(_("Has rumble strips"), null=True)
    owner = models.CharField(_("Owner"), max_length=254)
    symbol = models.CharField(_("Symbol"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = EnumField(
        LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True
    )
    lane_type = EnumField(
        LaneType, verbose_name=_("Lane type"), default=LaneType.MAIN, blank=True,
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

    def __str__(self):
        return f"{self.id} {self.device_type} {self.value}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.plan:
            self.plan.derive_location_from_related_plans()


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


class RoadMarkingReal(SoftDeleteModel, UserControlModel):
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
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
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
    has_rumble_strips = models.BooleanField(_("Has rumble strips"), null=True)
    owner = models.CharField(_("Owner"), max_length=254)
    symbol = models.CharField(_("Symbol"), max_length=254, blank=True, null=True)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )
    road_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    lane_number = EnumField(
        LaneNumber, verbose_name=_("Lane number"), default=LaneNumber.MAIN_1, blank=True
    )
    lane_type = EnumField(
        LaneType, verbose_name=_("Lane type"), default=LaneType.MAIN, blank=True,
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

    def __str__(self):
        return f"{self.id} {self.device_type} {self.value}"


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
