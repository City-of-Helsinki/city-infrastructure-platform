import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Self

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from enumfields import EnumField, EnumIntegerField

from admin_helper.decorators import requires_fields
from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.geometry_utils import geometry_is_legit
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


class ResponsibleEntityModel(models.Model):
    responsible_entity = models.ForeignKey(
        "traffic_control.ResponsibleEntity",
        verbose_name=_("Responsible entity"),
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text=_("Organization or project that this device is assigned to."),
    )

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True


class OwnedDeviceModel(models.Model):
    owner = models.ForeignKey(
        "traffic_control.Owner",
        verbose_name=_("Owner"),
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        help_text=_("Owner who orders and is responsible for the maintenance of the device."),
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

    @admin.display(description=_("Replaced"))
    @requires_fields(REPLACEMENT_TO_NEW)
    def is_replaced_as_str(self):
        return _("Yes") if hasattr(self, REPLACEMENT_TO_NEW) else _("No")


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


_DB_PLAN_ID_UNSET = object()


class UpdatePlanLocationMixin:
    """A mixin class that updates `Plan` location when the `plan` field of target model is changed.

    Affects only `Plan` objects with `derive_location` set to True.
    """

    @classmethod
    def from_db(cls, db: str, field_names: list[str], values: list[Any]) -> Self:
        """Load an instance from the database and cache its current plan FK id.

        The cached value is used in save() to detect plan changes without an
        additional database query.

        Args:
            db (str): The database alias the instance is being loaded from.
            field_names (list[str]): The field names present in values.
            values (list[Any]): The raw database values for the instance.

        Returns:
            Self: A new model instance with _db_plan_id cached.
        """
        instance = super().from_db(db, field_names, values)
        instance._db_plan_id = instance.plan_id
        return instance

    def save(self, *args, **kwargs) -> None:
        """Save the instance and trigger plan location derivation when the plan changes.

        Args:
            *args: Positional arguments forwarded to the parent save().
            **kwargs: Keyword arguments forwarded to the parent save().
        """
        if self._state.adding:
            old_plan = None
        else:
            old_plan = self._resolve_old_plan()
        super().save(*args, **kwargs)
        if self.plan != old_plan:
            if old_plan and old_plan.derive_location:
                old_plan.derive_location_from_related_plans()
            if self.plan and self.plan.derive_location:
                self.plan.derive_location_from_related_plans()

    def _resolve_old_plan(self) -> Optional[models.Model]:
        """Return the Plan instance assigned before the current save.

        Uses the plan_id cached by from_db to avoid an extra database query
        when the plan has not changed.

        Returns:
            Optional[models.Model]: The old Plan instance, or None.
        """
        db_plan_id = getattr(self, "_db_plan_id", _DB_PLAN_ID_UNSET)
        if db_plan_id is _DB_PLAN_ID_UNSET:
            return type(self).objects.get(pk=self.pk).plan
        if db_plan_id == self.plan_id:
            return self.plan
        return self._fetch_old_plan_by_id(db_plan_id)

    def _fetch_old_plan_by_id(self, plan_id: Any) -> Optional[models.Model]:
        """Fetch the Plan instance for the given plan_id.

        Args:
            plan_id (Any): The primary key of the Plan to fetch, or None.

        Returns:
            Optional[models.Model]: The matching Plan instance, or None if plan_id is None.
        """
        if plan_id is None:
            return None
        plan_model = type(self)._meta.get_field("plan").related_model
        return plan_model.objects.only("id", "derive_location").get(pk=plan_id)

    def delete(self, *args, **kwargs) -> None:
        """Delete the instance and trigger plan location derivation.

        Args:
            *args: Positional arguments forwarded to the parent delete().
            **kwargs: Keyword arguments forwarded to the parent delete().
        """
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
    is_public = models.BooleanField(
        _("Is public"),
        default=True,
        help_text=_("If unchecked, access is restricted to users/groups with appropriate table or file permissions"),
    )

    class Meta:
        abstract = True

    @requires_fields("file", "is_public")
    def __str__(self):
        if not self.is_public:
            return f"{self.file} (restricted)"
        return f"{self.file}"


class BoundaryCheckedLocationMixin:
    """A model mixin that does not allow geometry to be out of projection bounds.
    Checks that geometry is within SRID boundary.
    If WGS84 transformation when calculation WFS boundary box would fail if there are points outside..
    """

    GEOMETRY_FIELD_NAME = "location"

    def save(self, *args, **kwargs):
        geom = getattr(self, self.GEOMETRY_FIELD_NAME)
        if not geometry_is_legit(geom):
            raise ValidationError(f"Geometry for {self._meta.model_name} {self.location.ewkt} is not legal")

        super().save(*args, **kwargs)


class ValidityPeriodModel(models.Model):
    validity_period_start = models.DateField(
        _("Validity period start"),
        blank=True,
        null=True,
        help_text=_("Date on which this sign becomes active."),
    )
    validity_period_end = models.DateField(
        _("Validity period end"),
        blank=True,
        null=True,
        help_text=_("Date after which this sign becomes inactive."),
    )
    seasonal_validity_period_information = models.TextField(
        _("Seasonal validity period information"),
        blank=True,
        null=False,
        default="",
        help_text=_("Seasonal validity period information related to this device."),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Always set validity_period_start to plan's decision_date on save if plan exists and dates differ."""
        plan_decision_date = self.plan.decision_date if hasattr(self, "plan") and self.plan else None
        if plan_decision_date and plan_decision_date is not self.validity_period_start:
            self.validity_period_start = plan_decision_date
        super().save(*args, **kwargs)
