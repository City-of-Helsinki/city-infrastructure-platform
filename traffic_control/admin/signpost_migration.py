"""Django admin configuration for signpost migration tracking models."""
from django.contrib import admin
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from traffic_control.admin.common import (
    FIELD_POPULATION_APPEARANCE_FIELDSET,
    FIELD_POPULATION_LOCATION_FIELDSET,
    TrafficSignMigrationPlanRecordAdminMixin,
    TrafficSignMigrationRecordAdminMixin,
    TrafficSignMigrationRunAdminMixin,
)
from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)


class SignpostMigrationPlanRecordInline(admin.TabularInline):
    """Inline for viewing plan migration records within a run."""

    model = SignpostMigrationPlanRecord
    extra = 0
    can_delete = False
    fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "files_migrated",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        """Disable adding records through admin."""
        return False


class SignpostMigrationRealRecordInline(admin.TabularInline):
    """Inline for viewing real migration records within a run."""

    model = SignpostMigrationRealRecord
    extra = 0
    can_delete = False
    fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "plan_mapping_found",
        "files_migrated",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        """Disable adding records through admin."""
        return False


@admin.register(SignpostMigrationRun)
class SignpostTrafficSignMigrationRunAdmin(TrafficSignMigrationRunAdminMixin, admin.ModelAdmin):
    """Admin interface for signpost migration runs."""

    list_display = (
        "id",
        "started_at",
        "duration",
        "executed_by",
        "mode_display",
        "status_display",
        "plans_summary",
        "reals_summary",
        "device_types_updated",
    )
    list_filter = ("dry_run", "hard_delete", "success", "started_at")
    search_fields = ("id", "executed_by__username", "error_message")
    list_select_related = ("executed_by",)
    readonly_fields = (
        "id",
        "started_at",
        "completed_at",
        "duration",
        "executed_by",
        "dry_run",
        "hard_delete",
        "plans_processed",
        "plans_migrated",
        "reals_processed",
        "reals_migrated",
        "plan_files_migrated",
        "real_files_migrated",
        "device_types_updated",
        "error_message",
        "success",
        "lost_field_values_display",
        "plan_records_link",
        "real_records_link",
    )
    fieldsets = (
        (
            _("Run Information"),
            {
                "fields": (
                    "id",
                    "started_at",
                    "completed_at",
                    "duration",
                    "executed_by",
                    "dry_run",
                    "hard_delete",
                    "success",
                )
            },
        ),
        (
            _("Plan Migration Statistics"),
            {
                "fields": (
                    "plans_processed",
                    "plans_migrated",
                    "plan_files_migrated",
                    "plan_records_link",
                )
            },
        ),
        (
            _("Real Migration Statistics"),
            {
                "fields": (
                    "reals_processed",
                    "reals_migrated",
                    "real_files_migrated",
                    "real_records_link",
                )
            },
        ),
        (
            _("Device Types"),
            {"fields": ("device_types_updated",)},
        ),
        (
            _("Lost Data"),
            {
                "fields": ("lost_field_values_display",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Error Information"),
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = [SignpostMigrationPlanRecordInline, SignpostMigrationRealRecordInline]

    @admin.display(description=_("Plans"))
    def plans_summary(self, obj: SignpostMigrationRun) -> str:
        """Display plan migration summary."""
        if obj.plans_processed == 0:
            return "-"

        percentage = (obj.plans_migrated / obj.plans_processed * 100) if obj.plans_processed > 0 else 0

        return format_html(
            "<strong>{}/{}</strong> migrated ({}%)<br/>" '<small style="color: #6c757d;">{} files</small>',
            obj.plans_migrated,
            obj.plans_processed,
            int(percentage),
            obj.plan_files_migrated,
        )

    @admin.display(description=_("Reals"))
    def reals_summary(self, obj: SignpostMigrationRun) -> str:
        """Display real migration summary."""
        if obj.reals_processed == 0:
            return "-"

        percentage = (obj.reals_migrated / obj.reals_processed * 100) if obj.reals_processed > 0 else 0

        return format_html(
            "<strong>{}/{}</strong> migrated ({}%)<br/>" '<small style="color: #6c757d;">{} files</small>',
            obj.reals_migrated,
            obj.reals_processed,
            int(percentage),
            obj.real_files_migrated,
        )

    @admin.display(description=_("Plan Records"))
    def plan_records_link(self, obj: SignpostMigrationRun) -> str:
        """Create link to view all plan records for this run."""
        count = obj.plan_records.count()
        if count == 0:
            return "-"

        url = reverse(
            "admin:traffic_control_signpostmigrationplanrecord_changelist",
            query={"migration_run__id__exact": obj.id},
        )
        return format_html(
            '<a href="{}" style="font-weight: bold;">View {} plan record{}</a>',
            url,
            count,
            "s" if count != 1 else "",
        )

    @admin.display(description=_("Real Records"))
    def real_records_link(self, obj: SignpostMigrationRun) -> str:
        """Create link to view all real records for this run."""
        count = obj.real_records.count()
        if count == 0:
            return "-"

        url = reverse(
            "admin:traffic_control_signpostmigrationrealrecord_changelist",
            query={"migration_run__id__exact": obj.id},
        )
        return format_html(
            '<a href="{}" style="font-weight: bold;">View {} real record{}</a>',
            url,
            count,
            "s" if count != 1 else "",
        )

    @admin.display(description=_("Lost Field Values"))
    def lost_field_values_display(self, obj: SignpostMigrationRun) -> str:
        """Display lost field values in a formatted way."""
        all_lost_fields = [
            "surface_class",
            "peak_fastened",
            "affect_area",
            "installation_id",
            "installation_details",
            "permit_decision_id",
            "rfid",
            "operation",
            "attachment_url",
        ]
        lost_data = obj.lost_field_values or {}

        field_data = []
        for field in all_lost_fields:
            values = lost_data.get(field, [])
            field_data.append({"name": field, "values": values})

        context = {"fields": field_data}

        return render_to_string("admin/traffic_control/signpostmigrationrun/lost_field_values.html", context)


@admin.register(SignpostMigrationPlanRecord)
class SignpostMigrationPlanRecordAdmin(TrafficSignMigrationPlanRecordAdminMixin, admin.ModelAdmin):
    """Admin interface for plan migration detail records."""

    list_display = (
        "id",
        "migration_run_link",
        "device_type_code",
        "original_id_short",
        "new_id_short",
        "field_population_summary",
        "lost_data_summary",
        "files_migrated",
        "created_at",
    )
    list_filter = (
        "device_type_code",
        "migration_run__dry_run",
        "migration_run__success",
        "created_at",
    )
    search_fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "lost_surface_class",
    )
    list_select_related = ("migration_run", "original_traffic_sign_plan", "new_signpost_plan")
    readonly_fields = (
        "migration_run",
        "original_traffic_sign_plan",
        "new_signpost_plan",
        "original_id",
        "new_id",
        "device_type_code",
        "had_mount_plan",
        "had_plan",
        "had_height",
        "had_size",
        "had_direction",
        "had_reflection_class",
        "had_surface_class",
        "had_mount_type",
        "had_road_name",
        "had_lane_number",
        "had_lane_type",
        "had_location_specifier",
        "had_validity_period_start",
        "had_validity_period_end",
        "had_source_name",
        "had_source_id",
        "lost_surface_class",
        "lost_peak_fastened",
        "had_affect_area",
        "files_migrated",
        "created_at",
    )
    fieldsets = (
        (
            _("Migration Information"),
            {
                "fields": (
                    "migration_run",
                    "created_at",
                    "device_type_code",
                )
            },
        ),
        (
            _("Object IDs"),
            {
                "fields": (
                    "original_id",
                    "original_traffic_sign_plan",
                    "new_id",
                    "new_signpost_plan",
                )
            },
        ),
        (
            _("Field Population - Basic"),
            {
                "fields": (
                    "had_mount_plan",
                    "had_plan",
                    "had_height",
                    "had_size",
                    "had_direction",
                    "had_mount_type",
                )
            },
        ),
        FIELD_POPULATION_APPEARANCE_FIELDSET,
        FIELD_POPULATION_LOCATION_FIELDSET,
        (
            _("Field Population - Other"),
            {
                "fields": (
                    "had_validity_period_start",
                    "had_validity_period_end",
                    "had_source_name",
                    "had_source_id",
                )
            },
        ),
        (
            _("Lost Fields"),
            {
                "fields": (
                    "lost_surface_class",
                    "lost_peak_fastened",
                    "had_affect_area",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Files"),
            {"fields": ("files_migrated",)},
        ),
    )

    @admin.display(description=_("Migration Run"))
    def migration_run_link(self, obj: SignpostMigrationPlanRecord) -> str:
        """Create link to parent migration run."""
        url = reverse("admin:traffic_control_signpostmigrationrun_change", args=[obj.migration_run.id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.migration_run.id)

    @admin.display(description=_("Lost Data"))
    def lost_data_summary(self, obj: SignpostMigrationPlanRecord) -> str:
        """Display summary of lost data."""
        lost_items = []
        if obj.lost_surface_class:
            lost_items.append("surface_class")
        if obj.lost_peak_fastened:
            lost_items.append("peak_fastened")
        if obj.had_affect_area:
            lost_items.append("affect_area")

        if not lost_items:
            return mark_safe('<span style="color: #28a745;">None</span>')

        return format_html('<span style="color: #ffc107;">{}</span>', ", ".join(lost_items))


@admin.register(SignpostMigrationRealRecord)
class SignpostTrafficSignMigrationRealRecordAdmin(TrafficSignMigrationRecordAdminMixin, admin.ModelAdmin):
    """Admin interface for real migration detail records."""

    list_display = (
        "id",
        "migration_run_link",
        "device_type_code",
        "original_id_short",
        "new_id_short",
        "plan_mapping_status",
        "field_population_summary",
        "lost_data_summary",
        "files_migrated",
        "created_at",
    )
    list_filter = (
        "device_type_code",
        "plan_mapping_found",
        "migration_run__dry_run",
        "migration_run__success",
        "created_at",
    )
    search_fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "lost_surface_class",
        "lost_installation_id",
        "lost_permit_decision_id",
    )
    list_select_related = ("migration_run", "original_traffic_sign_real", "new_signpost_real")
    readonly_fields = (
        "migration_run",
        "original_traffic_sign_real",
        "new_signpost_real",
        "original_id",
        "new_id",
        "device_type_code",
        "plan_mapping_found",
        "had_mount_real",
        "had_traffic_sign_plan",
        "had_height",
        "had_size",
        "had_direction",
        "had_reflection_class",
        "had_surface_class",
        "had_mount_type",
        "had_road_name",
        "had_lane_number",
        "had_lane_type",
        "had_location_specifier",
        "had_legacy_code",
        "had_scanned_at",
        "had_manufacturer",
        "had_validity_period_start",
        "had_validity_period_end",
        "had_source_name",
        "had_source_id",
        "had_installation_status",
        "had_installation_date",
        "had_condition",
        "lost_surface_class",
        "lost_peak_fastened",
        "lost_installation_id",
        "lost_installation_details",
        "lost_permit_decision_id",
        "lost_rfid",
        "lost_operation",
        "lost_attachment_url",
        "files_migrated",
        "created_at",
    )
    fieldsets = (
        (
            _("Migration Information"),
            {
                "fields": (
                    "migration_run",
                    "created_at",
                    "device_type_code",
                )
            },
        ),
        (
            _("Object IDs"),
            {
                "fields": (
                    "original_id",
                    "original_traffic_sign_real",
                    "new_id",
                    "new_signpost_real",
                )
            },
        ),
        (
            _("Plan Mapping"),
            {
                "fields": (
                    "plan_mapping_found",
                    "had_traffic_sign_plan",
                )
            },
        ),
        (
            _("Field Population - Basic"),
            {
                "fields": (
                    "had_mount_real",
                    "had_height",
                    "had_size",
                    "had_direction",
                    "had_mount_type",
                )
            },
        ),
        FIELD_POPULATION_APPEARANCE_FIELDSET,
        FIELD_POPULATION_LOCATION_FIELDSET,
        (
            _("Field Population - Installation"),
            {
                "fields": (
                    "had_installation_status",
                    "had_installation_date",
                    "had_condition",
                )
            },
        ),
        (
            _("Field Population - Other"),
            {
                "fields": (
                    "had_legacy_code",
                    "had_scanned_at",
                    "had_manufacturer",
                    "had_validity_period_start",
                    "had_validity_period_end",
                    "had_source_name",
                    "had_source_id",
                )
            },
        ),
        (
            _("Lost Fields"),
            {
                "fields": (
                    "lost_surface_class",
                    "lost_peak_fastened",
                    "lost_installation_id",
                    "lost_installation_details",
                    "lost_permit_decision_id",
                    "lost_rfid",
                    "lost_operation",
                    "lost_attachment_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Files"),
            {"fields": ("files_migrated",)},
        ),
    )

    @admin.display(description=_("Migration Run"))
    def migration_run_link(self, obj: SignpostMigrationRealRecord) -> str:
        """Create link to parent migration run."""
        url = reverse("admin:traffic_control_signpostmigrationrun_change", args=[obj.migration_run.id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.migration_run.id)

    @admin.display(description=_("Plan Mapping"))
    def plan_mapping_status(self, obj: SignpostMigrationRealRecord) -> str:
        """Display plan mapping status."""
        if obj.plan_mapping_found:
            return mark_safe('<span style="color: #28a745;">✓ Mapped</span>')
        if obj.had_traffic_sign_plan:
            return mark_safe('<span style="color: #ffc107;">⚠ Not found</span>')
        return mark_safe('<span style="color: #6c757d;">- No plan</span>')

    @admin.display(description=_("Fields Populated"))
    def field_population_summary(self, obj: SignpostMigrationRealRecord) -> str:
        """Display summary of populated fields."""
        populated = sum(
            [
                obj.had_mount_real,
                obj.had_traffic_sign_plan,
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
                obj.had_legacy_code,
                obj.had_scanned_at,
                obj.had_manufacturer,
                obj.had_validity_period_start,
                obj.had_validity_period_end,
                obj.had_source_name,
                obj.had_source_id,
                obj.had_installation_status,
                obj.had_installation_date,
                obj.had_condition,
            ]
        )
        return self._render_field_population_html(populated, 20)

    @admin.display(description=_("Lost Data"))
    def lost_data_summary(self, obj: SignpostMigrationRealRecord) -> str:
        """Display summary of lost data."""
        lost_items = []
        if obj.lost_surface_class:
            lost_items.append("surface_class")
        if obj.lost_peak_fastened:
            lost_items.append("peak_fastened")
        if obj.lost_installation_id:
            lost_items.append("installation_id")
        if obj.lost_installation_details:
            lost_items.append("installation_details")
        if obj.lost_permit_decision_id:
            lost_items.append("permit_decision_id")
        if obj.lost_rfid:
            lost_items.append("rfid")
        if obj.lost_operation:
            lost_items.append("operation")
        if obj.lost_attachment_url:
            lost_items.append("attachment_url")

        if not lost_items:
            return mark_safe('<span style="color: #28a745;">None</span>')

        return format_html('<span style="color: #ffc107;">{}</span>', ", ".join(lost_items))
