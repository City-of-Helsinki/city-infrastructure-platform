import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from ..mixins.models import (
    SoftDeleteModel,
    SourceControlModel,
    UpdatePlanLocationMixin,
    UserControlModel,
)
from .common import Condition, InstallationStatus, Lifecycle
from .plan import Plan
from .utils import order_queryset_by_z_coord_desc, SoftDeleteQuerySet


class MountType(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
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
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
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


class MountPlan(
    UpdatePlanLocationMixin, SourceControlModel, SoftDeleteModel, UserControlModel
):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
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
    validity_period_start = models.DateField(
        _("Validity period start"), blank=True, null=True
    )
    validity_period_end = models.DateField(
        _("Validity period end"), blank=True, null=True
    )
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.PROTECT,
        related_name="mount_plans",
        blank=True,
        null=True,
    )
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    electric_accountable = models.CharField(
        _("Electric accountable"), max_length=254, blank=True, null=True
    )
    is_foldable = models.BooleanField(_("Is foldable"), blank=True, null=True)
    cross_bar_length = models.DecimalField(
        _("Cross bar length"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "mount_plan"
        verbose_name = _("Mount Plan")
        verbose_name_plural = _("Mount Plans")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return "%s %s" % (self.id, self.mount_type)


class MountPlanFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="planfiles/mount/"
    )
    mount_plan = models.ForeignKey(
        MountPlan, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "mount_plan_file"
        verbose_name = _("Mount Plan File")
        verbose_name_plural = _("Mount Plan Files")

    def __str__(self):
        return "%s" % self.file


class MountReal(SourceControlModel, SoftDeleteModel, UserControlModel):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
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
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        default=Condition.VERY_GOOD,
        blank=True,
        null=True,
    )
    inspected_at = models.DateTimeField(_("Inspected at"), blank=True, null=True)
    height = models.DecimalField(
        _("Height"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    txt = models.CharField(_("Txt"), max_length=254, blank=True, null=True)
    electric_accountable = models.CharField(
        _("Electric accountable"), max_length=254, blank=True, null=True
    )
    is_foldable = models.BooleanField(_("Is foldable"), blank=True, null=True)
    cross_bar_length = models.DecimalField(
        _("Cross bar length"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    diameter = models.DecimalField(
        _("Diameter"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "mount_real"
        verbose_name = _("Mount Real")
        verbose_name_plural = _("Mount Reals")
        unique_together = ["source_name", "source_id"]

    def __str__(self):
        return "%s %s" % (self.id, self.mount_type)

    @property
    def ordered_traffic_signs(self):
        """traffic sign reals ordered by z coordinate from top down"""
        qs = self.trafficsignreal_set.active()
        return order_queryset_by_z_coord_desc(qs)


class MountRealFile(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    file = models.FileField(
        _("File"), blank=False, null=False, upload_to="realfiles/mount/"
    )
    mount_real = models.ForeignKey(
        MountReal, on_delete=models.CASCADE, related_name="files"
    )

    class Meta:
        db_table = "mount_real_file"
        verbose_name = _("Mount Real File")
        verbose_name_plural = _("Mount Real Files")

    def __str__(self):
        return f"{self.file}"


auditlog.register(MountType)
auditlog.register(MountPlan)
auditlog.register(MountPlanFile)
auditlog.register(MountReal)
auditlog.register(MountRealFile)
