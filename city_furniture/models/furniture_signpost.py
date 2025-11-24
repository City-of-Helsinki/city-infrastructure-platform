from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from enumfields import EnumIntegerField

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType, CityFurnitureTarget
from traffic_control.mixins.models import (
    AbstractFileModel,
    BoundaryCheckedLocationMixin,
    InstalledDeviceModel,
    OwnedDeviceModel,
    ResponsibleEntityModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
    UUIDModel,
)
from traffic_control.models.common import OperationBase, OperationType
from traffic_control.models.mount import MountPlan, MountReal, MountType
from traffic_control.models.plan import Plan
from traffic_control.signal_utils import create_auditlog_signals_for_parent_model


class ArrowDirection(models.IntegerChoices):
    UP = 1, _("Up")
    DOWN = 2, _("Down")
    LEFT = 3, _("Left")
    RIGHT = 4, _("Right")
    TOP_RIGHT = 5, _("Top right")
    BOTTOM_RIGHT = 6, _("Bottom right")
    TOP_LEFT = 7, _("Top left")
    BOTTOM_LEFT = 8, _("Bottom left")


class FurnitureAbstractSignpost(
    BoundaryCheckedLocationMixin,
    SourceControlModel,
    SoftDeleteModel,
    UserControlModel,
    ResponsibleEntityModel,
    OwnedDeviceModel,
    UUIDModel,
):
    location = models.PointField(_("Location (3D)"), dim=3, srid=settings.SRID)
    location_name_fi = models.CharField(
        _("Finnish location name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Verbose name for the furniture signposts location in Finnish, e.g. street, park or island."),
    )
    location_name_sw = models.CharField(
        _("Swedish location name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Verbose name for the furniture signposts location in Swedish, e.g. street, park or island."),
    )
    location_name_en = models.CharField(
        _("English location name"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Verbose name for the furniture signposts location in English, e.g. street, park or island."),
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
        help_text=_("Type of the device from Helsinki Design Manual."),
    )
    # Size should be required if device type is non-standard
    size = models.CharField(
        _("Size"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Size of the signpost. Enter only if device has a non-standard size."),
    )
    height = models.DecimalField(
        _("Height"),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("The height of the sign from the ground, measured from the bottom in centimeters."),
    )
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Type of the mount this device is attached to."),
    )
    arrow_direction = EnumIntegerField(
        ArrowDirection,
        verbose_name=_("Arrow direction"),
        blank=True,
        null=True,
        help_text=_("Direction of the arrow on this device in relation to the sign."),
    )
    color = models.ForeignKey(
        CityFurnitureColor,
        verbose_name=_("Color"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Color of the device from Helsinki Design Manual."),
    )

    # Image on the sign
    pictogram = models.CharField(
        _("Pictogram"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Description of the pictogram on the sign."),
    )
    value = models.DecimalField(
        _("Furniture signpost value"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Numeric value on the sign."),
    )
    text_content_fi = models.TextField(
        _("Finnish text content"),
        blank=True,
        null=True,
        help_text=_("Content of the sign in Finnish."),
    )
    text_content_sw = models.TextField(
        _("Swedish text content"),
        blank=True,
        null=True,
        help_text=_("Content of the sign in Swedish."),
    )
    text_content_en = models.TextField(
        _("English text content"),
        blank=True,
        null=True,
        help_text=_("Content of the sign in English."),
    )
    content_responsible_entity = models.CharField(
        _("Content's responsible entity"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Entity responsible for the device's content."),
    )
    target = models.ForeignKey(
        CityFurnitureTarget,
        verbose_name=_("Target"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Target subject, which this device relates to."),
    )

    # Validity fields are required if device is temporary
    validity_period_start = models.DateField(
        _("Validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this device becomes active."),
    )
    validity_period_end = models.DateField(
        _("Validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this device becomes inactive."),
    )

    additional_material_url = models.CharField(
        _("Additional material URL"),
        max_length=254,
        blank=True,
        null=True,
        help_text=_("Additional material about the device. This should be publicly available."),
    )

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
        help_text=_("Mount that this device is mounted on."),
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Furniture Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Furniture Signpost inside which this device is located."),
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="furniture_signpost_plans",
        blank=True,
        null=True,
        help_text=_("Plan which this Device Plan is a part of."),
    )

    class Meta:
        db_table = "furniture_signpost_plan"
        verbose_name = _("Furniture Signpost Plan")
        verbose_name_plural = _("Furniture Signpost Plans")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
        ]


class FurnitureSignpostReal(FurnitureAbstractSignpost, InstalledDeviceModel):
    furniture_signpost_plan = models.ForeignKey(
        FurnitureSignpostPlan,
        verbose_name=_("Furniture Signpost Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("The plan for this device."),
    )
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent Furniture Signpost Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Furniture Signpost inside which this device is located."),
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("Mount Real"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        help_text=_("Mount that this device is mounted on."),
    )

    class Meta:
        db_table = "furniture_signpost_real"
        verbose_name = _("Furniture Signpost Real")
        verbose_name_plural = _("Furniture Signpost Reals")
        constraints = [
            models.UniqueConstraint(
                fields=["source_name", "source_id"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_source_name_id",
            ),
            models.UniqueConstraint(
                fields=["furniture_signpost_plan"],
                condition=models.Q(is_active=True),
                name="%(app_label)s_%(class)s_unique_furniture_signpost_plan_id",
            ),
        ]


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
auditlog.register(FurnitureSignpostPlanFile)
auditlog.register(FurnitureSignpostReal)
auditlog.register(FurnitureSignpostRealFile)

# Create signals for parent models
create_auditlog_signals_for_parent_model(FurnitureSignpostPlanFile, "furniture_signpost_plan")
create_auditlog_signals_for_parent_model(FurnitureSignpostRealFile, "furniture_signpost_real")
