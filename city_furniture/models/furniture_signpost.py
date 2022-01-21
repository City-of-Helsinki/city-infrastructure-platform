import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import Enum, EnumField, EnumIntegerField

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.mixins.models import (
    AbstractFileModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.common import OperationBase, OperationType
from traffic_control.models.mount import MountPlan, MountReal, MountType
from traffic_control.models.plan import Plan


class ArrowDirection(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    TOP_RIGHT = 5
    BOTTOM_RIGHT = 6
    TOP_LEFT = 7
    BOTTOM_LEFT = 8

    class Labels:
        UP = _("Up")
        DOWN = _("Down")
        LEFT = _("Left")
        RIGHT = _("Right")
        TOP_RIGHT = _("Top right")
        BOTTOM_RIGHT = _("Bottom right")
        TOP_LEFT = _("Top left")
        BOTTOM_LEFT = _("Bottom left")


class FurnitureAbstractSignpost(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    lifecycle = EnumIntegerField(Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE)

    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    location_name = models.CharField(_("Road name"), max_length=254, blank=True, null=True)
    direction = models.IntegerField(
        _("Direction"),
        default=0,
        help_text=_("The direction in which the person is standing, when looking directly at the sign."),
    )
    location_additional_info = models.CharField(
        _("Additional location info"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Additional information about the install location."),
    )
    device_type = models.ForeignKey(
        CityFurnitureDeviceType,
        verbose_name=_("City Furniture Device type"),
        on_delete=models.PROTECT,
        limit_choices_to=Q(
            Q(target_model=None) | Q(target_model=CityFurnitureDeviceTypeTargetModel.FURNITURE_SIGNPOST)
        ),
    )
    # Size should be required if device type is non-standard
    size = models.CharField(_("Size"), max_length=254, blank=True, null=True)
    height = models.DecimalField(_("Height"), max_digits=5, decimal_places=2, blank=True, null=True)
    order = models.SmallIntegerField(verbose_name=_("Order"), default=1)
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    arrow_direction = EnumIntegerField(ArrowDirection, verbose_name=_("Arrow direction"), blank=True, null=True)
    color = models.ForeignKey(
        CityFurnitureColor, verbose_name=_("Color"), on_delete=models.PROTECT, blank=True, null=True
    )

    # Image on the sign
    pictogram = models.CharField(_("Pictogram"), max_length=254, blank=True, null=True)
    value = models.DecimalField(_("Furniture signpost value"), max_digits=10, decimal_places=2, blank=True, null=True)
    text_content_fi = models.TextField(_("Finnish text content"), blank=True, null=True)
    text_content_sw = models.TextField(_("Swedish text content"), blank=True, null=True)
    text_content_en = models.TextField(_("English text content"), blank=True, null=True)
    content_responsible_entity = models.CharField(
        _("Content's responsible entity"), max_length=254, blank=True, null=True
    )

    target = models.ForeignKey(
        CityFurnitureTarget, verbose_name=_("Target"), on_delete=models.PROTECT, blank=True, null=True
    )

    # Validity fields are required if device is temporary
    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)

    project_id = models.CharField(_("External project ID"), max_length=254, blank=True, null=True)
    additional_material_url = models.CharField(_("Additional material URL"), max_length=254, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.id} {self.device_type} {self.text_content_fi}"

    def save(self, *args, **kwargs):
        if not self.device_type.validate_relation(CityFurnitureDeviceTypeTargetModel.FURNITURE_SIGNPOST):
            raise ValidationError(f'Device type "{self.device_type}" is not allowed for furniture signposts')

        super().save(*args, **kwargs)


class FurnitureSignpostPlan(UpdatePlanLocationMixin, FurnitureAbstractSignpost):
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Furniture Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="furniture_signpost_plans",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "furniture_signpost_plan"
        verbose_name = _("Furniture Signpost Plan")
        verbose_name_plural = _("Furniture Signpost Plans")
        unique_together = ["source_name", "source_id"]


class FurnitureSignpostReal(FurnitureAbstractSignpost):
    furniture_signpost_plan = models.ForeignKey(
        FurnitureSignpostPlan,
        verbose_name=_("Furniture Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Furniture Signpost Real"),
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

    class Meta:
        db_table = "furniture_signpost_real"
        verbose_name = _("Furniture Signpost Real")
        verbose_name_plural = _("Furniture Signpost Reals")
        unique_together = ["source_name", "source_id"]


class FurnitureSignpostRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"furniture_signpost": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    furniture_signpost_real = models.ForeignKey(
        FurnitureSignpostReal,
        verbose_name=_("Furniture Signpost Real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "furniture_signpost_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Furniture Signpost Real operation")
        verbose_name_plural = _("Furniture Signpost Real operations")


class FurnitureSignpostPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/furniture_signpost/")
    furniture_signpost_plan = models.ForeignKey(FurnitureSignpostPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "furniture_signpost_plan_file"
        verbose_name = _("Furniture Signpost Plan File")
        verbose_name_plural = _("Furniture Signpost Plan Files")


class FurnitureSignpostRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/furniture_signpost/")
    furniture_signpost_real = models.ForeignKey(FurnitureSignpostReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "furniture_signpost_real_file"
        verbose_name = _("Furniture Signpost Real File")
        verbose_name_plural = _("Furniture Signpost Real Files")


auditlog.register(FurnitureSignpostPlan)
auditlog.register(FurnitureSignpostReal)
