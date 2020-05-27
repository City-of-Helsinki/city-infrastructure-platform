import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from ..mixins.models import SoftDeleteModelMixin
from .common import Condition, InstallationStatus, Lifecycle
from .plan import Plan
from .utils import order_queryset_by_z_coord_desc, SoftDeleteQuerySet


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


class MountPlan(SoftDeleteModelMixin, models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    type = models.CharField(
        verbose_name=_("Mount type"), max_length=20, default="PORTAL"
    )
    portal_type = models.ForeignKey(
        PortalType,
        verbose_name=_("Portal type"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    material = models.CharField(_("Material"), max_length=254, blank=True, null=True)
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
    plan = models.ForeignKey(
        Plan,
        verbose_name=_("Plan"),
        on_delete=models.CASCADE,
        related_name="mount_plans",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_mount_plan_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_mount_plan_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_mount_plan_set",
        on_delete=models.CASCADE,
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
    owner = models.CharField(_("Owner"), max_length=254)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "mount_plan"
        verbose_name = _("Mount Plan")
        verbose_name_plural = _("Mount Plans")

    def __str__(self):
        return "%s %s" % (self.id, self.type)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.plan:
            self.plan.derive_location_from_related_plans()


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


class MountReal(SoftDeleteModelMixin, models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    mount_plan = models.ForeignKey(
        MountPlan,
        verbose_name=_("Mount Plan"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    location = models.GeometryField(_("Location (2D)"), srid=settings.SRID)
    type = models.CharField(
        verbose_name=_("Mount type"), max_length=20, default="PORTAL"
    )
    portal_type = models.ForeignKey(
        PortalType,
        verbose_name=_("Portal type"),
        on_delete=models.CASCADE,
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
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    inspected_at = models.DateTimeField(_("Inspected at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_mount_real_set",
        on_delete=models.CASCADE,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_mount_real_set",
        on_delete=models.CASCADE,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_mount_real_set",
        on_delete=models.CASCADE,
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
    diameter = models.DecimalField(
        _("Diameter"), max_digits=5, decimal_places=2, blank=True, null=True
    )
    owner = models.CharField(_("Owner"), max_length=254)
    lifecycle = EnumIntegerField(
        Lifecycle, verbose_name=_("Lifecycle"), default=Lifecycle.ACTIVE
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "mount_real"
        verbose_name = _("Mount Real")
        verbose_name_plural = _("Mount Reals")

    def __str__(self):
        return "%s %s" % (self.id, self.type)

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


auditlog.register(MountPlan)
auditlog.register(MountPlanFile)
auditlog.register(MountReal)
auditlog.register(MountRealFile)
