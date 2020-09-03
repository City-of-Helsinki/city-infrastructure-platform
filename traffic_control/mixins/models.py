from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class SoftDeleteModel(models.Model):
    is_active = models.BooleanField(_("Active"), default=True)
    deleted_at = models.DateTimeField(_("Deleted at"), blank=True, null=True)
    deleted_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Deleted by"),
        related_name="deleted_by_%(class)s_set",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

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
        on_delete=models.PROTECT,
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Updated by"),
        related_name="updated_by_%(class)s_set",
        on_delete=models.PROTECT,
    )

    class Meta:
        abstract = True


class UpdatePlanLocationMixin:
    """A mixin class that updates plan location when the plan
    field of target model is changed"""

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
            if old_plan:
                old_plan.derive_location_from_related_plans()
            if self.plan:
                self.plan.derive_location_from_related_plans()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.plan:
            self.plan.derive_location_from_related_plans()


class SourceControlModel(models.Model):
    source_id = models.CharField(
        _("Source id"), max_length=64, null=True, blank=True, default=None
    )
    source_name = models.CharField(
        _("Source name"), max_length=254, null=True, blank=True, default=None
    )

    class Meta:
        abstract = True
