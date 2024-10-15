import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.models.utils import SoftDeleteQuerySet

logger = logging.getLogger("traffic_control")

REPLACEMENT_TO_NEW = "replacement_to_new"
REPLACEMENT_TO_OLD = "replacement_to_old"


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(_("Active"), default=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_%(class)s_set",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self, user):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()


class UserControlModel(models.Model):
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_%(class)s_set",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_%(class)s_set",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True


class OwnedDeviceModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        help_text=_("Owner who orders and is responsible for the maintenance of the device."),
    )
    responsible_entity = models.ForeignKey(
        "traffic_control.ResponsibleEntity",
        verbose_name=_("Responsible entity"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text=_("Organization or project that this device is assigned to."),
    )
    lifecycle = EnumIntegerField(
        Lifecycle,
        verbose_name=_("Lifecycle"),
        default=Lifecycle.ACTIVE,
        help_text=_("Lifecycle of the device, which describes the activity status of the device."),
    )

    class Meta:
        abstract = True


class ReplaceableDevicePlanMixin:
    @property
    def replaced_by(self) -> Optional[models.Model]:
        """Return the device plan that replaces this device plan"""
        if hasattr(self, REPLACEMENT_TO_NEW):
            return getattr(self, REPLACEMENT_TO_NEW).new
        return None

    @property
    def replaces(self) -> Optional[models.Model]:
        """Return the device plan that this device plan replaces"""
        if hasattr(self, REPLACEMENT_TO_OLD):
            return getattr(self, REPLACEMENT_TO_OLD).old
        return None

    @property
    def is_replaced(self):
        """Return `True` if this device plan has been replaced by another device plan"""
        return hasattr(self, REPLACEMENT_TO_NEW)

    @property
    @admin.display(description=_("Replaced"))
    def is_replaced_as_str(self):
        return _("Yes") if self.is_replaced else _("No")


class InstalledDeviceModel(models.Model):
    installation_date = models.DateField(
        _("Installation date"),
        blank=True,
        null=True,
        help_text=_("Date on which this device was installed on."),
    )
    installation_status = EnumField(
        InstallationStatus,
        verbose_name=_("Installation status"),
        max_length=10,
        blank=True,
        null=True,
        help_text=_("Describes this devices installation status."),
    )
    condition = EnumIntegerField(
        Condition,
        verbose_name=_("Condition"),
        blank=True,
        null=True,
        help_text=_("Describes the condition of this device."),
    )

    class Meta:
        abstract = True


class UpdatePlanLocationMixin:
    """
    A mixin class that updates `Plan` location when the `plan` field of target model is changed.
    Affects only `Plan` objects with `derive_location` set to True.
    """

    def save(self, *args, **kwargs):
        if self._state.adding:
            old_plan = None
        else:
            # remember the old plan when updating existing traffic
            # control objects
            old_plan = type(self).objects.get(pk=self.pk).plan
        super().save(*args, **kwargs)
        if self.plan != old_plan:
            # note that we also need to update the old plan location when
            # updating the plan field of existing traffic control objects.
            if old_plan and old_plan.derive_location:
                old_plan.derive_location_from_related_plans()
            if self.plan and self.plan.derive_location:
                self.plan.derive_location_from_related_plans()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.plan and self.plan.derive_location:
            self.plan.derive_location_from_related_plans()


class SourceControlModel(models.Model):
    source_id = models.CharField(
        _("Source id"),
        max_length=64,
        null=True,
        blank=True,
        default=None,
        help_text=_("ID of the device in the source where this device was imported from."),
    )
    source_name = models.CharField(
        _("Source name"),
        max_length=254,
        null=True,
        blank=True,
        default=None,
        help_text=_("Name of the source for where this device was imported from."),
    )

    class Meta:
        abstract = True


class DecimalValueFromDeviceTypeMixin:
    """
    A model mixin class that saves device type value to the decimal value field

    Only set value field when the value field is empty and a default value
    is set in device type
    """

    def save(self, *args, **kwargs):
        if not self.value and self.device_type and self.device_type.value:
            try:
                self.value = Decimal(self.device_type.value)
            except InvalidOperation:
                logger.warning("Cannot convert device type value to Decimal")
        super().save(*args, **kwargs)


class AbstractFileModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.file}"
