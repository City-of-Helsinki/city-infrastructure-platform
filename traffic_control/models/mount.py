import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from traffic_control.enums import Condition, InstallationStatus
from traffic_control.mixins.models import (
    AbstractFileModel,
    OwnedDeviceModel,
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from traffic_control.models.common import OperationBase, OperationType
from traffic_control.models.plan import Plan
from traffic_control.models.utils import order_queryset_by_z_coord_desc


class MountType(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    code = models.CharField(
        verbose_name=_("Code"),
        max_length=128,
        blank=False,
        null=False,
    )
    description = models.CharField(
        verbose_name=_("Description"),
        max_length=256,
        blank=False,
        null=False,
    )
    description_fi = models.CharField(
        verbose_name=_("Description (fi)"),
        max_length=256,
        blank=True,
        null=False,
    )
    digiroad_code = models.IntegerField(
        verbose_name=_("Digiroad code"),
        blank=True,
        null=True,
    )
    digiroad_description = models.CharField(
        verbose_name=_("Digiroad description"),
        max_length=256,
        blank=True,
    )

    class Meta:
        db_table = "mount_type"
        verbose_name = _("Mount type")
        verbose_name_plural = _("Mount types")

    def __str__(self):
        return f"{self.description} ({self.code})"


class PortalType(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    structure = models.CharField(_("Portal structure"), max_length=64)
    build_type = models.CharField(_("Portal build type"), max_length=64)
    model = models.CharField(_("Portal model"), max_length=64)

    class Meta:
        db_table = "portal_type"
        verbose_name = _("Portal type")
        verbose_name_plural = _("Portal types")
        unique_together = ("structure", "build_type", "model")

    def __str__(self):
        return "%s - %s - %s" % (self.structure, self.build_type, self.model)


class AbstractMount(SourceControlModel, SoftDeleteModel, UserControlModel, OwnedDeviceModel):
    location = models.GeometryField(_("Location (3D)"), dim=3, srid=settings.SRID)
    height = models.DecimalField(_("Height"), max_digits=5, decimal_places=2, blank=True, null=True)
    mount_type = models.ForeignKey(
        MountType,
        verbose_name=_("Mount type"),
        blank=False,
        null=True,
        on_delete=models.PROTECT,
    )
    base = models.CharField(verbose_name=_("Base"), max_length=128, blank=True)
    portal_type = models.ForeignKey(
        PortalType,
        verbose_name=_("Portal type"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
    validity_period_start = models.DateField(_("Validity period start"), blank=True, null=True)
    validity_period_end = models.DateField(_("Validity period end"), blank=True, null=True)
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    electric_accountable = models.CharField(_("Electric accountable"), max_length=254, blank=True, null=True)
    is_foldable = models.BooleanField(_("Is foldable"), blank=True, null=True)
    cross_bar_length = models.DecimalField(_("Cross bar length"), max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.id} {self.mount_type}"


class MountPlan(UpdatePlanLocationMixin, AbstractMount):
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="mount_plans",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "mount_plan"
        verbose_name = _("Mount Plan")
        verbose_name_plural = _("Mount Plans")
        unique_together = ["source_name", "source_id"]


class MountReal(AbstractMount):
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    inspected_at = models.DateTimeField(_("Inspected at"), blank=True, null=True)
    diameter = models.DecimalField(_("Diameter"), max_digits=5, decimal_places=2, blank=True, null=True)
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
        db_table = "mount_real"
        verbose_name = _("Mount Real")
        verbose_name_plural = _("Mount Reals")
        unique_together = ["source_name", "source_id"]

    @property
    def ordered_traffic_signs(self):
        """traffic sign reals ordered by z coordinate from top down"""
        qs = self.trafficsignreal_set.active()
        return order_queryset_by_z_coord_desc(qs)


class MountRealOperation(OperationBase):
    operation_type = models.ForeignKey(
        OperationType,
        limit_choices_to={"mount": True},
        verbose_name=_("operation type"),
        on_delete=models.PROTECT,
    )
    mount_real = models.ForeignKey(
        MountReal,
        verbose_name=_("mount real"),
        on_delete=models.PROTECT,
        related_name="operations",
    )

    class Meta:
        db_table = "mount_real_operation"
        ordering = ["operation_date"]
        verbose_name = _("Mount real operation")
        verbose_name_plural = _("Mount real operations")


class MountPlanFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="planfiles/mount/")
    mount_plan = models.ForeignKey(MountPlan, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "mount_plan_file"
        verbose_name = _("Mount Plan File")
        verbose_name_plural = _("Mount Plan Files")


class MountRealFile(AbstractFileModel):
    file = models.FileField(_("File"), blank=False, null=False, upload_to="realfiles/mount/")
    mount_real = models.ForeignKey(MountReal, on_delete=models.CASCADE, related_name="files")

    class Meta:
        db_table = "mount_real_file"
        verbose_name = _("Mount Real File")
        verbose_name_plural = _("Mount Real Files")


auditlog.register(MountType)
auditlog.register(MountPlan)
auditlog.register(MountPlanFile)
auditlog.register(MountReal)
auditlog.register(MountRealFile)
