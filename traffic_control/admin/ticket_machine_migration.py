"""Django admin configuration for ticket machine migration tracking models."""
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from traffic_control.models.ticket_machine_migration import (
    TicketMachineMigrationPlanRecord,
    TicketMachineMigrationRealRecord,
    TicketMachineMigrationRun,
)


class TicketMachineMigrationPlanRecordInline(admin.TabularInline):
    """Inline for viewing plan migration records within a run."""

    model = TicketMachineMigrationPlanRecord
    extra = 0
    can_delete = False
    fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "parent_found",
        "parent_sign_code",
        "multiple_parents_found",
        "files_migrated",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        """Disable adding records through admin."""
        return False


class TicketMachineMigrationRealRecordInline(admin.TabularInline):
    """Inline for viewing real migration records within a run."""

    model = TicketMachineMigrationRealRecord
    extra = 0
    can_delete = False
    fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "parent_found",
        "parent_sign_code",
        "plan_mapping_found",
        "multiple_parents_found",
        "files_migrated",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        """Disable adding records through admin."""
        return False


@admin.register(TicketMachineMigrationRun)
class TicketMachineMigrationRunAdmin(admin.ModelAdmin):
    """Admin interface for ticket machine migration runs."""

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
        "plans_with_parent",
        "plans_without_parent",
        "reals_processed",
        "reals_migrated",
        "reals_with_parent",
        "reals_without_parent",
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
                    "plans_with_parent",
                    "plans_without_parent",
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
                    "reals_with_parent",
                    "reals_without_parent",
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
    inlines = [TicketMachineMigrationPlanRecordInline, TicketMachineMigrationRealRecordInline]

    def has_add_permission(self, request):
        """Disable manual creation of migration runs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only allow deletion of failed or dry-run migrations."""
        # First check base permissions
        if not super().has_delete_permission(request, obj):
            return False
        # Then apply custom logic: only allow deletion of failed or dry-run migrations
        if obj:
            return not obj.success or obj.dry_run
        return True

    @admin.action(description="Delete selected migration runs (dry-run/failed only)")
    def delete_selected_migration_runs(self, request, queryset):
        """Delete selected migration runs (dry-run/failed only)."""
        deletable = queryset.filter(models.Q(dry_run=True) | models.Q(success=False))
        protected = queryset.exclude(models.Q(dry_run=True) | models.Q(success=False))

        deletable_count = deletable.count()
        protected_count = protected.count()

        if protected_count > 0:
            self.message_user(
                request,
                f"Cannot delete {protected_count} successful non-dry-run migration(s). "
                f"Only dry-run and failed migrations can be deleted to preserve audit trail.",
                level="warning",
            )

        if deletable_count > 0:
            deletable.delete()
            self.message_user(
                request,
                f"Successfully deleted {deletable_count} migration run(s).",
                level="success",
            )

    actions = ["delete_selected_migration_runs"]

    @admin.display(description=_("Mode"))
    def mode_display(self, obj: TicketMachineMigrationRun) -> str:
        """Display migration mode with colored badge."""
        if obj.dry_run:
            return mark_safe(
                '<span style="background-color: #ffc107; color: #000; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">DRY RUN</span>'
            )
        elif obj.hard_delete:
            return mark_safe(
                '<span style="background-color: #dc3545; color: #fff; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">HARD DELETE</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #28a745; color: #fff; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">SOFT DELETE</span>'
            )

    @admin.display(description=_("Status"))
    def status_display(self, obj: TicketMachineMigrationRun) -> str:
        """Display status with colored badge."""
        if obj.success and obj.dry_run:
            return mark_safe(
                '<span style="background-color: #17a2b8; color: #fff; padding: 3px 8px; '
                'border-radius: 3px;">✓ DRY RUN SUCCESS</span>'
            )
        elif obj.success:
            return mark_safe(
                '<span style="background-color: #28a745; color: #fff; padding: 3px 8px; '
                'border-radius: 3px;">✓ SUCCESS</span>'
            )
        elif obj.error_message:
            return mark_safe(
                '<span style="background-color: #dc3545; color: #fff; padding: 3px 8px; '
                'border-radius: 3px;">✗ FAILED</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #6c757d; color: #fff; padding: 3px 8px; '
                'border-radius: 3px;">⋯ IN PROGRESS</span>'
            )

    @admin.display(description=_("Duration"))
    def duration(self, obj: TicketMachineMigrationRun) -> str:
        """Calculate and display migration duration."""
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"

    @admin.display(description=_("Plans"))
    def plans_summary(self, obj: TicketMachineMigrationRun) -> str:
        """Display plan migration summary."""
        if obj.plans_processed == 0:
            return "-"

        percentage = (obj.plans_migrated / obj.plans_processed * 100) if obj.plans_processed > 0 else 0
        parent_percentage = (obj.plans_with_parent / obj.plans_processed * 100) if obj.plans_processed > 0 else 0

        return format_html(
            "<strong>{}/{}</strong> migrated ({}%)<br/>"
            '<small style="color: #28a745;">✓ {} with parent ({}%)</small><br/>'
            '<small style="color: #6c757d;">○ {} without parent</small>',
            obj.plans_migrated,
            obj.plans_processed,
            int(percentage),
            obj.plans_with_parent,
            int(parent_percentage),
            obj.plans_without_parent,
        )

    @admin.display(description=_("Reals"))
    def reals_summary(self, obj: TicketMachineMigrationRun) -> str:
        """Display real migration summary."""
        if obj.reals_processed == 0:
            return "-"

        percentage = (obj.reals_migrated / obj.reals_processed * 100) if obj.reals_processed > 0 else 0
        parent_percentage = (obj.reals_with_parent / obj.reals_processed * 100) if obj.reals_processed > 0 else 0

        return format_html(
            "<strong>{}/{}</strong> migrated ({}%)<br/>"
            '<small style="color: #28a745;">✓ {} with parent ({}%)</small><br/>'
            '<small style="color: #6c757d;">○ {} without parent</small>',
            obj.reals_migrated,
            obj.reals_processed,
            int(percentage),
            obj.reals_with_parent,
            int(parent_percentage),
            obj.reals_without_parent,
        )

    @admin.display(description=_("Plan Records"))
    def plan_records_link(self, obj: TicketMachineMigrationRun) -> str:
        """Create link to view all plan records for this run."""
        count = obj.plan_records.count()
        if count == 0:
            return "-"

        url = reverse(
            "admin:traffic_control_ticketmachinemigrationplanrecord_changelist",
            query={"migration_run__id__exact": obj.id},
        )
        return format_html(
            '<a href="{}" style="font-weight: bold;">View {} plan record{}</a>',
            url,
            count,
            "s" if count != 1 else "",
        )

    @admin.display(description=_("Real Records"))
    def real_records_link(self, obj: TicketMachineMigrationRun) -> str:
        """Create link to view all real records for this run."""
        count = obj.real_records.count()
        if count == 0:
            return "-"

        url = reverse(
            "admin:traffic_control_ticketmachinemigrationrealrecord_changelist",
            query={"migration_run__id__exact": obj.id},
        )
        return format_html(
            '<a href="{}" style="font-weight: bold;">View {} real record{}</a>',
            url,
            count,
            "s" if count != 1 else "",
        )

    @admin.display(description=_("Lost Field Values"))
    def lost_field_values_display(self, obj: TicketMachineMigrationRun) -> str:
        """Display lost field values in a formatted way."""
        # Define all possible lost fields
        all_lost_fields = ["value", "txt", "double_sided", "peak_fastened", "affect_area"]

        if not obj.lost_field_values:
            # No data tracked yet, show all fields as empty
            output = []
            for field in all_lost_fields:
                output.append(f'<strong>{field}</strong>: <span style="color: #28a745;">No data lost</span>')
            return mark_safe("<br/>".join(output))

        output = []
        for field in all_lost_fields:
            values = obj.lost_field_values.get(field, [])
            if values:
                value_count = len(values)
                all_values = ", ".join(str(v) for v in values)
                output.append(f"<strong>{field}</strong> ({value_count} unique): {all_values}")
            else:
                output.append(f'<strong>{field}</strong>: <span style="color: #28a745;">No data lost</span>')

        return mark_safe("<br/>".join(output))


@admin.register(TicketMachineMigrationPlanRecord)
class TicketMachineMigrationPlanRecordAdmin(admin.ModelAdmin):
    """Admin interface for plan migration detail records."""

    list_display = (
        "id",
        "migration_run_link",
        "device_type_code",
        "original_id_short",
        "new_id_short",
        "parent_status",
        "field_population_summary",
        "lost_data_summary",
        "files_migrated",
        "created_at",
    )
    list_filter = (
        "device_type_code",
        "parent_found",
        "multiple_parents_found",
        "migration_run__dry_run",
        "migration_run__success",
        "created_at",
    )
    search_fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "parent_sign_code",
        "lost_value",
        "lost_txt",
    )
    list_select_related = ("migration_run", "original_traffic_sign_plan", "new_additional_sign_plan")
    readonly_fields = (
        "migration_run",
        "original_traffic_sign_plan",
        "new_additional_sign_plan",
        "original_id",
        "new_id",
        "device_type_code",
        "parent_found",
        "parent_sign_id",
        "parent_sign_code",
        "multiple_parents_found",
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
        "lost_value",
        "lost_txt",
        "lost_double_sided",
        "lost_peak_fastened",
        "had_affect_area",
        "set_color_to_blue",
        "set_content_s_null",
        "set_missing_content_false",
        "set_additional_information_empty",
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
                    "new_additional_sign_plan",
                )
            },
        ),
        (
            _("Parent Assignment"),
            {
                "fields": (
                    "parent_found",
                    "parent_sign_id",
                    "parent_sign_code",
                    "multiple_parents_found",
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
        (
            _("Field Population - Appearance"),
            {
                "fields": (
                    "had_reflection_class",
                    "had_surface_class",
                )
            },
        ),
        (
            _("Field Population - Location"),
            {
                "fields": (
                    "had_road_name",
                    "had_lane_number",
                    "had_lane_type",
                    "had_location_specifier",
                )
            },
        ),
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
                    "lost_value",
                    "lost_txt",
                    "lost_double_sided",
                    "lost_peak_fastened",
                    "had_affect_area",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Default Values Set"),
            {
                "fields": (
                    "set_color_to_blue",
                    "set_content_s_null",
                    "set_missing_content_false",
                    "set_additional_information_empty",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Files"),
            {"fields": ("files_migrated",)},
        ),
    )

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

    @admin.action(description="Delete selected records (from dry-run/failed migrations only)")
    def delete_selected_records(self, request, queryset):
        """Delete selected records (from dry-run/failed migrations only)."""
        deletable = queryset.filter(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))
        protected = queryset.exclude(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))

        deletable_count = deletable.count()
        protected_count = protected.count()

        if protected_count > 0:
            self.message_user(
                request,
                f"Cannot delete {protected_count} record(s) from successful non-dry-run migrations. "
                f"Only records from dry-run and failed migrations can be deleted.",
                level="warning",
            )

        if deletable_count > 0:
            deletable.delete()
            self.message_user(
                request,
                f"Successfully deleted {deletable_count} plan record(s).",
                level="success",
            )

    actions = ["delete_selected_records"]

    @admin.display(description=_("Migration Run"))
    def migration_run_link(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Create link to parent migration run."""
        url = reverse("admin:traffic_control_ticketmachinemigrationrun_change", args=[obj.migration_run.id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.migration_run.id)

    @admin.display(description=_("Original ID"))
    def original_id_short(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Display shortened original ID."""
        return str(obj.original_id)[:8] + "..."

    @admin.display(description=_("New ID"))
    def new_id_short(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Display shortened new ID."""
        if obj.new_id:
            return str(obj.new_id)[:8] + "..."
        return "-"

    @admin.display(description=_("Parent"))
    def parent_status(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Display parent assignment status."""
        if obj.parent_found:
            style = "color: #28a745; font-weight: bold;"
            warning = " ⚠" if obj.multiple_parents_found else ""
            return format_html('<span style="{}">✓ {}{}</span>', style, obj.parent_sign_code, warning)
        return mark_safe('<span style="color: #6c757d;">○ No parent</span>')

    @admin.display(description=_("Fields Populated"))
    def field_population_summary(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Display summary of populated fields."""
        total_fields = 16
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
        percentage = int((populated / total_fields) * 100)
        return format_html('<span style="font-weight: bold;">{}/{}</span> ({}%)', populated, total_fields, percentage)

    @admin.display(description=_("Lost Data"))
    def lost_data_summary(self, obj: TicketMachineMigrationPlanRecord) -> str:
        """Display summary of lost data."""
        lost_items = []
        if obj.lost_value:
            lost_items.append("value")
        if obj.lost_txt:
            lost_items.append("txt")
        if obj.lost_double_sided:
            lost_items.append("double_sided")
        if obj.lost_peak_fastened:
            lost_items.append("peak_fastened")
        if obj.had_affect_area:
            lost_items.append("affect_area")

        if not lost_items:
            return mark_safe('<span style="color: #28a745;">None</span>')

        return format_html('<span style="color: #ffc107;">{}</span>', ", ".join(lost_items))


@admin.register(TicketMachineMigrationRealRecord)
class TicketMachineMigrationRealRecordAdmin(admin.ModelAdmin):
    """Admin interface for real migration detail records."""

    list_display = (
        "id",
        "migration_run_link",
        "device_type_code",
        "original_id_short",
        "new_id_short",
        "parent_status",
        "plan_mapping_status",
        "field_population_summary",
        "lost_data_summary",
        "files_migrated",
        "created_at",
    )
    list_filter = (
        "device_type_code",
        "parent_found",
        "plan_mapping_found",
        "multiple_parents_found",
        "migration_run__dry_run",
        "migration_run__success",
        "created_at",
    )
    search_fields = (
        "original_id",
        "new_id",
        "device_type_code",
        "parent_sign_code",
        "lost_value",
        "lost_txt",
    )
    list_select_related = ("migration_run", "original_traffic_sign_real", "new_additional_sign_real")
    readonly_fields = (
        "migration_run",
        "original_traffic_sign_real",
        "new_additional_sign_real",
        "original_id",
        "new_id",
        "device_type_code",
        "parent_found",
        "parent_sign_id",
        "parent_sign_code",
        "multiple_parents_found",
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
        "had_installation_id",
        "had_installation_details",
        "had_permit_decision_id",
        "had_scanned_at",
        "had_manufacturer",
        "had_rfid",
        "had_operation",
        "had_attachment_url",
        "had_validity_period_start",
        "had_validity_period_end",
        "had_source_name",
        "had_source_id",
        "had_installation_status",
        "had_installation_date",
        "had_installation_status_note",
        "lost_value",
        "lost_txt",
        "lost_double_sided",
        "lost_peak_fastened",
        "set_color_to_blue",
        "set_content_s_null",
        "set_missing_content_false",
        "set_additional_information_empty",
        "set_installed_by_null",
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
                    "new_additional_sign_real",
                )
            },
        ),
        (
            _("Parent Assignment"),
            {
                "fields": (
                    "parent_found",
                    "parent_sign_id",
                    "parent_sign_code",
                    "multiple_parents_found",
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
        (
            _("Field Population - Appearance"),
            {
                "fields": (
                    "had_reflection_class",
                    "had_surface_class",
                )
            },
        ),
        (
            _("Field Population - Location"),
            {
                "fields": (
                    "had_road_name",
                    "had_lane_number",
                    "had_lane_type",
                    "had_location_specifier",
                )
            },
        ),
        (
            _("Field Population - Installation"),
            {
                "fields": (
                    "had_installation_id",
                    "had_installation_details",
                    "had_installation_status",
                    "had_installation_date",
                    "had_installation_status_note",
                )
            },
        ),
        (
            _("Field Population - Other"),
            {
                "fields": (
                    "had_legacy_code",
                    "had_permit_decision_id",
                    "had_scanned_at",
                    "had_manufacturer",
                    "had_rfid",
                    "had_operation",
                    "had_attachment_url",
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
                    "lost_value",
                    "lost_txt",
                    "lost_double_sided",
                    "lost_peak_fastened",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Default Values Set"),
            {
                "fields": (
                    "set_color_to_blue",
                    "set_content_s_null",
                    "set_missing_content_false",
                    "set_additional_information_empty",
                    "set_installed_by_null",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Files"),
            {"fields": ("files_migrated",)},
        ),
    )

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

    @admin.action(description="Delete selected records (from dry-run/failed migrations only)")
    def delete_selected_records(self, request, queryset):
        """Delete selected records (from dry-run/failed migrations only)."""
        deletable = queryset.filter(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))
        protected = queryset.exclude(models.Q(migration_run__dry_run=True) | models.Q(migration_run__success=False))

        deletable_count = deletable.count()
        protected_count = protected.count()

        if protected_count > 0:
            self.message_user(
                request,
                f"Cannot delete {protected_count} record(s) from successful non-dry-run migrations. "
                f"Only records from dry-run and failed migrations can be deleted.",
                level="warning",
            )

        if deletable_count > 0:
            deletable.delete()
            self.message_user(
                request,
                f"Successfully deleted {deletable_count} real record(s).",
                level="success",
            )

    actions = ["delete_selected_records"]

    @admin.display(description=_("Migration Run"))
    def migration_run_link(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Create link to parent migration run."""
        url = reverse("admin:traffic_control_ticketmachinemigrationrun_change", args=[obj.migration_run.id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.migration_run.id)

    @admin.display(description=_("Original ID"))
    def original_id_short(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display shortened original ID."""
        return str(obj.original_id)[:8] + "..."

    @admin.display(description=_("New ID"))
    def new_id_short(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display shortened new ID."""
        if obj.new_id:
            return str(obj.new_id)[:8] + "..."
        return "-"

    @admin.display(description=_("Parent"))
    def parent_status(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display parent assignment status."""
        if obj.parent_found:
            style = "color: #28a745; font-weight: bold;"
            warning = " ⚠" if obj.multiple_parents_found else ""
            return format_html('<span style="{}">✓ {}{}</span>', style, obj.parent_sign_code, warning)
        return mark_safe('<span style="color: #6c757d;">○ No parent</span>')

    @admin.display(description=_("Plan Mapping"))
    def plan_mapping_status(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display plan mapping status."""
        if obj.plan_mapping_found:
            return mark_safe('<span style="color: #28a745;">✓ Mapped</span>')
        elif obj.had_traffic_sign_plan:
            return mark_safe('<span style="color: #ffc107;">⚠ Not found</span>')
        return mark_safe('<span style="color: #6c757d;">- No plan</span>')

    @admin.display(description=_("Fields Populated"))
    def field_population_summary(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display summary of populated fields."""
        total_fields = 27
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
                obj.had_installation_id,
                obj.had_installation_details,
                obj.had_permit_decision_id,
                obj.had_scanned_at,
                obj.had_manufacturer,
                obj.had_rfid,
                obj.had_operation,
                obj.had_attachment_url,
                obj.had_validity_period_start,
                obj.had_validity_period_end,
                obj.had_source_name,
                obj.had_source_id,
                obj.had_installation_status,
                obj.had_installation_date,
            ]
        )
        percentage = int((populated / total_fields) * 100)
        return format_html('<span style="font-weight: bold;">{}/{}</span> ({}%)', populated, total_fields, percentage)

    @admin.display(description=_("Lost Data"))
    def lost_data_summary(self, obj: TicketMachineMigrationRealRecord) -> str:
        """Display summary of lost data."""
        lost_items = []
        if obj.lost_value:
            lost_items.append("value")
        if obj.lost_txt:
            lost_items.append("txt")
        if obj.lost_double_sided:
            lost_items.append("double_sided")
        if obj.lost_peak_fastened:
            lost_items.append("peak_fastened")

        if not lost_items:
            return mark_safe('<span style="color: #28a745;">None</span>')

        return format_html('<span style="color: #ffc107;">{}</span>', ", ".join(lost_items))
