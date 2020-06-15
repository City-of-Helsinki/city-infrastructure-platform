import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from ..mixins.models import SoftDeleteModel, UserControlModel
from .common import (
    Color,
    Condition,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    Reflection,
    Size,
    Surface,
    TrafficControlDeviceType,
)
from .mount import MountPlan, MountReal, MountType
from .plan import Plan
from .utils import SoftDeleteQuerySet


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


class TrafficSignPlan(SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=20, decimal_places=6, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Plan"),
        on_delete=models.PROTECT,
        related_name="children",
        blank=True,
        null=True,
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
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
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )
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
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254)
    color = EnumIntegerField(
        Color, verbose_name=_("Color"), default=Color.BLUE, blank=True, null=True
    )
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
        default=LocationSpecifier.RIGHT,
        blank=True,
        null=True,
    )
    source_id = models.CharField(_("Source id"), max_length=64, blank=True, null=True)
    source_name = models.CharField(
        _("Source name"), max_length=254, blank=True, null=True
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_plan"
        verbose_name = _("Traffic Sign Plan")
        verbose_name_plural = _("Traffic Sign Plans")

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.plan:
            self.plan.derive_location_from_related_plans()


class TrafficSignPlanFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="planfiles/traffic_sign/"
    )
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "traffic_sign_plan_file"
        verbose_name = _("Traffic Sign Plan File")
        verbose_name_plural = _("Traffic Sign Plan Files")

    def __str__(self):
        return "%s" % self.file


class TrafficSignReal(SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Traffic Sign Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    height = models.DecimalField(
        _("Height"), max_digits=20, decimal_places=6, blank=True, null=True
    )
    direction = models.IntegerField(_("Direction"), default=0)
    device_type = models.ForeignKey(
        TrafficControlDeviceType,
        verbose_name=_("Device type"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    value = models.IntegerField(_("Traffic Sign Code value"), blank=True, null=True)
    legacy_code = models.CharField(
        _("Legacy Traffic Sign Code"), max_length=32, blank=True, null=True
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Traffic Sign Real"),
        on_delete=models.PROTECT,
        related_name="children",
        blank=True,
        null=True,
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    installation_date = models.DateField(_("Installation date"), blank=True, null=True)
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        blank=True,
        null=True,
    )
    installation_id = models.CharField(
        _("Installation id"), max_length=254, blank=True, null=True
    )
    installation_details = models.CharField(
        _("Installation details"), max_length=254, blank=True, null=True
    )
    allu_decision_id = models.CharField(
        _("Decision id (Allu)"), max_length=254, blank=True, null=True
    )
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    condition = EnumIntegerField(
        Condition, verbose_name=_("Condition"), blank=True, null=True,
    )
    affect_area = models.PolygonField(
        _("Affect area (2D)"), srid=settings.SRID, blank=True, null=True
    )
    scanned_at = models.DateTimeField(_("Scanned at"), blank=True, null=True)
    size = EnumField(Size, verbose_name=_("Size"), max_length=1, blank=True, null=True,)
    reflection_class = EnumField(
        Reflection, verbose_name=_("Reflection"), max_length=2, blank=True, null=True,
    )
    surface_class = EnumField(
        Surface, verbose_name=_("Surface"), max_length=6, blank=True, null=True,
    )
    seasonal_validity_period_start = models.DateField(
        _("Seasonal validity period start"), blank=True, null=True
    )
    seasonal_validity_period_end = models.DateField(
        _("Seasonal validity period end"), blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254)
    manufacturer = models.CharField(
        _("Manufacturer"), max_length=254, blank=True, null=True
    )
    rfid = models.CharField(_("RFID"), max_length=254, blank=True, null=True)
    color = EnumIntegerField(Color, verbose_name=_("Color"), blank=True, null=True)
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
        LocationSpecifier, verbose_name=_("Location specifier"), blank=True, null=True,
    )
    operation = models.CharField(_("Operation"), max_length=64, blank=True, null=True)
    attachment_url = models.URLField(
        _("Attachment url"), max_length=500, blank=True, null=True
    )
    source_id = models.CharField(_("Source id"), max_length=64, blank=True, null=True)
    source_name = models.CharField(
        _("Source name"), max_length=254, blank=True, null=True
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "traffic_sign_real"
        verbose_name = _("Traffic Sign Real")
        verbose_name_plural = _("Traffic Sign Reals")

    def __str__(self):
        return f"{self.id} {self.device_type}"

    def save(self, *args, **kwargs):
        if not self.device_type:
            self.device_type = (
                TrafficControlDeviceType.objects.filter(legacy_code=self.legacy_code)
                .order_by("code")
                .first()
            )
        super().save(*args, **kwargs)

    def has_additional_signs(self):
        return self.children.active().exists()

    @transaction.atomic
    def soft_delete(self, user):
        super().soft_delete(user)
        for additional_sign in self.children.active():
            additional_sign.soft_delete(user)


class TrafficSignRealFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="realfiles/traffic_sign/"
    )
    traffic_sign_real = models.ForeignKey(
        TrafficSignReal, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "traffic_sign_real_file"
        verbose_name = _("Traffic Sign Real File")
        verbose_name_plural = _("Traffic Sign Real Files")

    def __str__(self):
        return f"{self.file}"


auditlog.register(TrafficSignPlan)
auditlog.register(TrafficSignReal)
