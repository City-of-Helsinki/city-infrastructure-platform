from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from traffic_control.admin.utils import PermissionInlineMixin
from traffic_control.enums import TRAFFIC_SIGN_TYPE_CHOICES
from traffic_control.models import OperationalArea, OperationType
from traffic_control.services.common import get_all_not_replaced_plans, get_all_replaced_plans

__all__ = (
    "TrafficSignMigrationRecordAdminMixin",
    "TrafficSignMigrationPlanRecordAdminMixin",
    "TrafficSignMigrationRunAdminMixin",
    "FIELD_POPULATION_APPEARANCE_FIELDSET",
    "FIELD_POPULATION_LOCATION_FIELDSET",
    "TrafficControlOperationInlineBase",
    "OperationalAreaListFilter",
    "ReplacesInline",
    "ReplacedByInline",
    "PlanReplacementListFilterMixin",
    "TrafficSignTypeListFilterBase",
    "TrafficSignTypeCodeFilter",
    "DeviceTypeSignTypeListFilter",
)


FIELD_POPULATION_APPEARANCE_FIELDSET = (
    _("Field Population - Appearance"),
    {
        "fields": (
            "had_reflection_class",
            "had_surface_class",
        )
    },
)

FIELD_POPULATION_LOCATION_FIELDSET = (
    _("Field Population - Location"),
    {
        "fields": (
            "had_road_name",
            "had_lane_number",
            "had_lane_type",
            "had_location_specifier",
        )
    },
)


class TrafficSignMigrationRecordAdminMixin:
    """Mixin for shared admin functionality between Plan and Real record admins."""

    def has_add_permission(self, request):
        """Disable manual creation of records."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion if parent run was dry-run or failed."""
        # First check base permissions
        if not super().has_delete_permission(request, obj):
            return False
        # Then apply custom logic: only allow if parent run was dry-run or failed
        if obj and obj.migration_run:
            return obj.migration_run.dry_run or not obj.migration_run.success
        return True

    def delete_queryset(self, request, queryset):
        """
        Override deletion to only allow deleting records from dry-run or failed migrations.

        This is called by Django's built-in "delete selected objects" action.
        """
        # Filter to only deletable records (from dry-run or failed migrations)
        deletable = queryset.filter(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))
        protected = queryset.exclude(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))

        protected_count = protected.count()
        if protected_count > 0:
            self.message_user(
                request,
                f"Cannot delete {protected_count} record(s) from successful non-dry-run migrations. "
                f"Only records from dry-run and failed migrations can be deleted.",
                level="warning",
            )

        # Delete only the deletable records using parent's method
        if deletable.exists():
            super().delete_queryset(request, deletable)

    @admin.display(description=_("Original ID"))
    def original_id_short(self, obj) -> str:
        """Display shortened original ID."""
        return str(obj.original_id)[:8] + "..."

    @admin.display(description=_("New ID"))
    def new_id_short(self, obj) -> str:
        """Display shortened new ID."""
        if obj.new_id:
            return str(obj.new_id)[:8] + "..."
        return "-"

    @staticmethod
    def _render_field_population_html(populated: int, total_fields: int) -> str:
        """Render the field population summary as HTML."""

        percentage = int((populated / total_fields) * 100) if total_fields > 0 else 0
        return format_html('<span style="font-weight: bold;">{}/{}</span> ({}%)', populated, total_fields, percentage)


class TrafficSignMigrationPlanRecordAdminMixin(TrafficSignMigrationRecordAdminMixin):
    """Mixin for plan migration record admins with shared field_population_summary."""

    @admin.display(description=_("Fields Populated"))
    def field_population_summary(self, obj) -> str:
        """Display summary of populated fields (14 common fields + mount_plan + plan)."""
        populated = sum(
            [
                obj.had_mount_plan,
                obj.had_plan,
                obj.had_height,
                obj.had_size,
                obj.had_direction,
                obj.had_reflection_class,
                obj.had_surface_class,
                obj.had_mount_type,
                obj.had_road_name,
                obj.had_lane_number,
                obj.had_lane_type,
                obj.had_location_specifier,
                obj.had_validity_period_start,
                obj.had_validity_period_end,
                obj.had_source_name,
                obj.had_source_id,
            ]
        )
        return self._render_field_population_html(populated, 16)


class TrafficSignMigrationRunAdminMixin:
    """Mixin for shared admin functionality for migration run admins."""

    def has_add_permission(self, request):
        """Disable manual creation of migration runs."""
        return False

    @admin.display(description=_("Duration"))
    def duration(self, obj) -> str:
        """Calculate and display migration duration.

        Args:
            obj: The migration run instance.

        Returns:
            str: Formatted duration string or '-' if not completed.
        """
        if not (obj.completed_at and obj.started_at):
            return "-"
        delta = obj.completed_at - obj.started_at
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    @admin.display(description=_("Mode"))
    def mode_display(self, obj) -> str:
        """Display migration mode with colored badge.

        Args:
            obj: The migration run instance.

        Returns:
            str: HTML span with colored mode badge.
        """
        if obj.dry_run:
            return mark_safe(
                '<span style="background-color: #ffc107; color: #000; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">DRY RUN</span>'
            )
        if obj.hard_delete:
            return mark_safe(
                '<span style="background-color: #dc3545; color: #fff; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">HARD DELETE</span>'
            )
        return mark_safe(
            '<span style="background-color: #28a745; color: #fff; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">SOFT DELETE</span>'
        )

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion of failed or dry-run migrations."""
        if not super().has_delete_permission(request, obj):
            return False
        if obj:
            return not obj.success or obj.dry_run
        return True

    def delete_queryset(self, request, queryset):
        """
        Override deletion to only allow deleting dry-run or failed migrations.

        This is called by Django's built-in "delete selected objects" action.
        """
        deletable = queryset.filter(models.Q(dry_run=True) | models.Q(success=False))
        protected = queryset.exclude(models.Q(dry_run=True) | models.Q(success=False))

        protected_count = protected.count()
        if protected_count > 0:
            self.message_user(
                request,
                f"Cannot delete {protected_count} successful non-dry-run migration(s). "
                f"Only dry-run and failed migrations can be deleted to preserve audit trail.",
                level="warning",
            )

        if deletable.exists():
            super().delete_queryset(request, deletable)

    @admin.display(description=_("Status"))
    def status_display(self, obj) -> str:
        """Display status with colored badge.

        Args:
            obj: The migration run instance.

        Returns:
            str: HTML span with colored status badge.
        """
        if obj.success and obj.dry_run:
            bg, text = "#17a2b8", "✓ DRY RUN SUCCESS"
        elif obj.success:
            bg, text = "#28a745", "✓ SUCCESS"
        elif obj.error_message:
            bg, text = "#dc3545", "✗ FAILED"
        else:
            bg, text = "#6c757d", "⋯ IN PROGRESS"
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 3px;">{}</span>',
            bg,
            text,
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
