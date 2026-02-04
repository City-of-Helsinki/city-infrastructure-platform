from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from traffic_control.admin.utils import PermissionInlineMixin
from traffic_control.enums import TRAFFIC_SIGN_TYPE_CHOICES
from traffic_control.models import OperationalArea, OperationType
from traffic_control.services.common import get_all_not_replaced_plans, get_all_replaced_plans

__all__ = (
    "TrafficControlOperationInlineBase",
    "OperationalAreaListFilter",
    "ReplacesInline",
    "ReplacedByInline",
    "PlanReplacementListFilterMixin",
    "TrafficSignTypeListFilterBase",
    "TrafficSignTypeCodeFilter",
    "DeviceTypeSignTypeListFilter",
)


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "traffic_sign",
        "additional_sign",
        "road_marking",
        "barrier",
        "signpost",
        "traffic_light",
        "mount",
    )


class TrafficControlOperationInlineBase(admin.TabularInline):
    extra = 0
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")


class OperationalAreaListFilter(SimpleListFilter):
    title = _("Operational area")
    parameter_name = "operational_area"

    def lookups(self, request, model_admin):
        return OperationalArea.objects.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            operational_area = OperationalArea.objects.get(id=self.value())
            return queryset.filter(location__contained=operational_area.location)


class ReplacesInline(PermissionInlineMixin, admin.StackedInline):
    fk_name = "new"
    verbose_name = _("Replaces")
    raw_id_fields = ("old",)
    # TODO: Modifying replacements can be allowed when Admin UI uses service layer functions
    readonly_fields = ("old",)


class ReplacedByInline(PermissionInlineMixin, admin.StackedInline):
    fk_name = "old"
    verbose_name = _("Replaced by")
    raw_id_fields = ("new",)
    readonly_fields = ("new",)


class PlanReplacementListFilterMixin:
    title = _("Replaced")
    parameter_name = "plan_replacement"

    def lookups(self, request, model_admin):
        return (
            (False, _("No")),
            (True, _("Yes")),
        )

    def queryset(self, request, queryset):
        value = self.value() or None
        if value == "True":
            return queryset.filter(id__in=get_all_replaced_plans(self.plan_model))
        if value == "False":
            return queryset.filter(id__in=get_all_not_replaced_plans(self.plan_model))


class TrafficSignTypeListFilterBase(SimpleListFilter):
    """Base filter for traffic sign type filtering by device type code prefix."""

    title = _("Traffic sign type")
    parameter_name = "traffic_sign_type"

    def lookups(self, request, model_admin):
        """
        Returns traffic sign type choices.

        Args:
            request: The HTTP request object.
            model_admin: The model admin instance.

        Returns:
            tuple: Traffic sign type choices (code prefix, description).
        """
        return TRAFFIC_SIGN_TYPE_CHOICES


class TrafficSignTypeCodeFilter(TrafficSignTypeListFilterBase):
    """Filter for TrafficControlDeviceType admin filtering directly on code field."""

    def queryset(self, request, queryset):
        """
        Filters queryset by device type code prefix.

        Args:
            request: The HTTP request object.
            queryset: The queryset to filter.

        Returns:
            QuerySet: Filtered queryset or original if no filter value.
        """
        value = self.value()
        if value:
            return queryset.filter(code__startswith=value)
        return queryset


class DeviceTypeSignTypeListFilter(TrafficSignTypeListFilterBase):
    """Filter for models with device_type FK filtering on device_type__code field."""

    def queryset(self, request, queryset):
        """
        Filters queryset by device type code prefix through FK relationship.

        Args:
            request: The HTTP request object.
            queryset: The queryset to filter.

        Returns:
            QuerySet: Filtered queryset or original if no filter value.
        """
        value = self.value()
        if value:
            return queryset.filter(device_type__code__startswith=value)
        return queryset
