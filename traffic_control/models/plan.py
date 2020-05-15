import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from ..mixins.models import SoftDeleteModelMixin
from ..models.utils import SoftDeleteQuerySet


class Plan(SoftDeleteModelMixin, models.Model):
    # Permissions
    ADD_PERMISSION = "traffic_control.add_plan"
    CHANGE_PERMISSION = "traffic_control.change_plan"
    DELETE_PERMISSION = "traffic_control.delete_plan"
    VIEW_PERMISSION = "traffic_control.view_plan"

    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )

    name = models.CharField(verbose_name=_("Name"), max_length=512)
    plan_number = models.CharField(
        verbose_name=_("Plan number"),
        max_length=16,
        help_text=_("Year and verdict section separated with an underscore."),
    )
    location = models.MultiPolygonField(_("Location (2D)"), srid=settings.SRID)
    planner = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Planner"),
        related_name="plan_set",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )
    decision_maker = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Decision maker"),
        related_name="decision_maker_plan_set",
        on_delete=models.PROTECT,
        null=False,
        blank=False,
    )

    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Created by"),
        related_name="created_by_plan_set",
        on_delete=models.PROTECT,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_plan_set",
        on_delete=models.PROTECT,
    )
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_plan_set",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        db_table = "plan"
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")

    def __str__(self):
        return f"{self.plan_number} {self.name}"


auditlog.register(Plan)
