"""Models for tracking ticket machine migration from traffic_sign to additional_sign tables."""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from traffic_control.models.additional_sign import AdditionalSignPlan, AdditionalSignReal
from traffic_control.models.traffic_sign import TrafficSignPlan, TrafficSignReal

User = get_user_model()


class BaseFieldTrackingMixin(models.Model):
    """Abstract base class for common field tracking across Plan and Real records."""

    # Common field tracking (fields that exist in both TrafficSignPlan and TrafficSignReal)
    had_height = models.BooleanField(_("Had height"), default=False)
    had_size = models.BooleanField(_("Had size"), default=False)
    had_direction = models.BooleanField(_("Had direction"), default=False)
    had_reflection_class = models.BooleanField(_("Had reflection_class"), default=False)
    had_surface_class = models.BooleanField(_("Had surface_class"), default=False)
    had_mount_type = models.BooleanField(_("Had mount_type"), default=False)
    had_road_name = models.BooleanField(_("Had road_name"), default=False)
    had_lane_number = models.BooleanField(_("Had lane_number"), default=False)
    had_lane_type = models.BooleanField(_("Had lane_type"), default=False)
    had_location_specifier = models.BooleanField(_("Had location_specifier"), default=False)
    had_validity_period_start = models.BooleanField(_("Had validity_period_start"), default=False)
    had_validity_period_end = models.BooleanField(_("Had validity_period_end"), default=False)
    had_source_name = models.BooleanField(_("Had source_name"), default=False)
    had_source_id = models.BooleanField(_("Had source_id"), default=False)

    # Common lost fields
    lost_value = models.CharField(_("Lost value"), max_length=50, blank=True, default="")
    lost_txt = models.CharField(_("Lost txt"), max_length=254, blank=True, default="")
    lost_double_sided = models.BooleanField(_("Lost double_sided"), default=False)
    lost_peak_fastened = models.BooleanField(_("Lost peak_fastened"), default=False)

    # Common default values set
    set_color_to_blue = models.BooleanField(_("Set color to BLUE"), default=True)
    set_content_s_null = models.BooleanField(_("Set content_s to null"), default=True)
    set_missing_content_false = models.BooleanField(_("Set missing_content to false"), default=True)
    set_additional_information_empty = models.BooleanField(_("Set additional_information to empty"), default=True)

    files_migrated = models.IntegerField(
        _("Files migrated"),
        default=0,
        help_text=_("Number of file attachments migrated."),
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        abstract = True


class TicketMachineMigrationRun(models.Model):
    """Tracks each execution of the ticket machine migration command."""

    id = models.BigAutoField(primary_key=True)
    started_at = models.DateTimeField(
        _("Started at"),
        auto_now_add=True,
        help_text=_("Timestamp when the migration command started."),
    )
    completed_at = models.DateTimeField(
        _("Completed at"),
        blank=True,
        null=True,
        help_text=_("Timestamp when the migration command completed successfully."),
    )
    executed_by = models.ForeignKey(
        User,
        verbose_name=_("Executed by"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("User who executed the migration command."),
    )
    dry_run = models.BooleanField(
        _("Dry run"),
        default=False,
        help_text=_("Whether this was a dry run (no actual changes made)."),
    )
    hard_delete = models.BooleanField(
        _("Hard delete"),
        default=False,
        help_text=_("Whether hard-delete mode was used (true) or soft-delete (false)."),
    )
    plans_processed = models.IntegerField(
        _("Plans processed"),
        default=0,
        help_text=_("Total number of TrafficSignPlan objects processed."),
    )
    plans_migrated = models.IntegerField(
        _("Plans migrated"),
        default=0,
        help_text=_("Number of TrafficSignPlan objects successfully migrated."),
    )
    plans_with_parent = models.IntegerField(
        _("Plans with parent"),
        default=0,
        help_text=_("Number of plans that were assigned a parent sign (E2/521)."),
    )
    plans_without_parent = models.IntegerField(
        _("Plans without parent"),
        default=0,
        help_text=_("Number of plans that had no parent sign found."),
    )
    reals_processed = models.IntegerField(
        _("Reals processed"),
        default=0,
        help_text=_("Total number of TrafficSignReal objects processed."),
    )
    reals_migrated = models.IntegerField(
        _("Reals migrated"),
        default=0,
        help_text=_("Number of TrafficSignReal objects successfully migrated."),
    )
    reals_with_parent = models.IntegerField(
        _("Reals with parent"),
        default=0,
        help_text=_("Number of reals that were assigned a parent sign (E2/521)."),
    )
    reals_without_parent = models.IntegerField(
        _("Reals without parent"),
        default=0,
        help_text=_("Number of reals that had no parent sign found."),
    )
    device_types_updated = models.IntegerField(
        _("Device types updated"),
        default=0,
        help_text=_("Number of device types with target_model updated."),
    )
    error_message = models.TextField(
        _("Error message"),
        blank=True,
        default="",
        help_text=_("Error message if the migration failed."),
    )
    success = models.BooleanField(
        _("Success"),
        default=False,
        help_text=_("Whether the migration completed successfully."),
    )
    lost_field_values = models.JSONField(
        _("Lost field values"),
        default=dict,
        blank=True,
        help_text=_(
            "Dictionary of field names to sets of unique values that were lost during migration. "
            "Example: {'value': ['10', '20'], 'txt': ['Info text'], 'affect_area': ['had_polygon']}"
        ),
    )

    class Meta:
        db_table = "ticket_machine_migration_run"
        verbose_name = _("Ticket Machine Migration Run")
        verbose_name_plural = _("Ticket Machine Migration Runs")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        """Return string representation."""
        # Determine status
        if self.success:
            status = "Success"
        elif self.error_message:
            status = "Failed"
        else:
            status = "In Progress"

        # Determine mode
        if self.dry_run:
            mode = "DRY RUN"
        elif self.hard_delete:
            mode = "HARD DELETE"
        else:
            mode = "SOFT DELETE"

        return f"{self.started_at.strftime('%Y-%m-%d %H:%M:%S')} - {status} ({mode})"


class TicketMachineMigrationPlanRecord(BaseFieldTrackingMixin):
    """Detailed record of each TrafficSignPlan to AdditionalSignPlan migration."""

    id = models.BigAutoField(primary_key=True)
    migration_run = models.ForeignKey(
        TicketMachineMigrationRun,
        verbose_name=_("Migration run"),
        on_delete=models.CASCADE,
        related_name="plan_records",
        help_text=_("The migration run this record belongs to."),
    )
    original_traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Original TrafficSignPlan"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The original TrafficSignPlan that was migrated."),
    )
    new_additional_sign_plan = models.ForeignKey(
        AdditionalSignPlan,
        verbose_name=_("New AdditionalSignPlan"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The newly created AdditionalSignPlan."),
    )
    original_id = models.UUIDField(
        _("Original ID"),
        help_text=_("UUID of the original TrafficSignPlan (preserved even if deleted)."),
    )
    new_id = models.UUIDField(
        _("New ID"),
        blank=True,
        null=True,
        help_text=_("UUID of the new AdditionalSignPlan."),
    )
    device_type_code = models.CharField(
        _("Device type code"),
        max_length=32,
        help_text=_("Device type code of the ticket machine."),
    )
    parent_found = models.BooleanField(
        _("Parent found"),
        default=False,
        help_text=_("Whether a parent sign (E2/521) was found and assigned."),
    )
    parent_sign_id = models.UUIDField(
        _("Parent sign ID"),
        blank=True,
        null=True,
        help_text=_("UUID of the parent TrafficSignPlan if found."),
    )
    parent_sign_code = models.CharField(
        _("Parent sign code"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("Device type code of the parent sign (E2 or 521)."),
    )
    multiple_parents_found = models.BooleanField(
        _("Multiple parents found"),
        default=False,
        help_text=_("Whether multiple E2/521 signs were found on the same mount."),
    )
    # Plan-specific field tracking
    had_mount_plan = models.BooleanField(_("Had mount_plan"), default=False)
    had_plan = models.BooleanField(_("Had plan"), default=False)
    # Common fields inherited from BaseFieldTrackingMixin
    had_affect_area = models.BooleanField(_("Had affect_area"), default=False)

    class Meta:
        db_table = "ticket_machine_migration_plan_record"
        verbose_name = _("Ticket Machine Migration Plan Record")
        verbose_name_plural = _("Ticket Machine Migration Plan Records")
        ordering = ["migration_run", "created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        parent_status = f"with parent {self.parent_sign_code}" if self.parent_found else "no parent"
        return f"Plan {self.original_id} → {self.new_id} ({parent_status})"


class TicketMachineMigrationRealRecord(BaseFieldTrackingMixin):
    """Detailed record of each TrafficSignReal to AdditionalSignReal migration."""

    id = models.BigAutoField(primary_key=True)
    migration_run = models.ForeignKey(
        TicketMachineMigrationRun,
        verbose_name=_("Migration run"),
        on_delete=models.CASCADE,
        related_name="real_records",
        help_text=_("The migration run this record belongs to."),
    )
    original_traffic_sign_real = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("Original TrafficSignReal"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The original TrafficSignReal that was migrated."),
    )
    new_additional_sign_real = models.ForeignKey(
        AdditionalSignReal,
        verbose_name=_("New AdditionalSignReal"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The newly created AdditionalSignReal."),
    )
    original_id = models.UUIDField(
        _("Original ID"),
        help_text=_("UUID of the original TrafficSignReal (preserved even if deleted)."),
    )
    new_id = models.UUIDField(
        _("New ID"),
        blank=True,
        null=True,
        help_text=_("UUID of the new AdditionalSignReal."),
    )
    device_type_code = models.CharField(
        _("Device type code"),
        max_length=32,
        help_text=_("Device type code of the ticket machine."),
    )
    parent_found = models.BooleanField(
        _("Parent found"),
        default=False,
        help_text=_("Whether a parent sign (E2/521) was found and assigned."),
    )
    parent_sign_id = models.UUIDField(
        _("Parent sign ID"),
        blank=True,
        null=True,
        help_text=_("UUID of the parent TrafficSignReal if found."),
    )
    parent_sign_code = models.CharField(
        _("Parent sign code"),
        max_length=32,
        blank=True,
        null=True,
        help_text=_("Device type code of the parent sign (E2 or 521)."),
    )
    multiple_parents_found = models.BooleanField(
        _("Multiple parents found"),
        default=False,
        help_text=_("Whether multiple E2/521 signs were found on the same mount."),
    )
    plan_mapping_found = models.BooleanField(
        _("Plan mapping found"),
        default=False,
        help_text=_("Whether a corresponding AdditionalSignPlan was found for traffic_sign_plan."),
    )
    # Real-specific field tracking (not in TrafficSignPlan)
    had_mount_real = models.BooleanField(_("Had mount_real"), default=False)
    had_traffic_sign_plan = models.BooleanField(_("Had traffic_sign_plan"), default=False)
    had_legacy_code = models.BooleanField(_("Had legacy_code"), default=False)
    had_installation_id = models.BooleanField(_("Had installation_id"), default=False)
    had_installation_details = models.BooleanField(_("Had installation_details"), default=False)
    had_permit_decision_id = models.BooleanField(_("Had permit_decision_id"), default=False)
    had_scanned_at = models.BooleanField(_("Had scanned_at"), default=False)
    had_manufacturer = models.BooleanField(_("Had manufacturer"), default=False)
    had_rfid = models.BooleanField(_("Had rfid"), default=False)
    had_operation = models.BooleanField(_("Had operation"), default=False)
    had_attachment_url = models.BooleanField(_("Had attachment_url"), default=False)
    had_installation_status = models.BooleanField(_("Had installation_status"), default=False)
    had_installation_date = models.BooleanField(_("Had installation_date"), default=False)
    had_installation_status_note = models.BooleanField(_("Had installation_status_note"), default=False)
    # Common fields inherited from BaseFieldTrackingMixin
    set_installed_by_null = models.BooleanField(_("Set installed_by to null"), default=True)

    class Meta:
        db_table = "ticket_machine_migration_real_record"
        verbose_name = _("Ticket Machine Migration Real Record")
        verbose_name_plural = _("Ticket Machine Migration Real Records")
        ordering = ["migration_run", "created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        parent_status = f"with parent {self.parent_sign_code}" if self.parent_found else "no parent"
        return f"Real {self.original_id} → {self.new_id} ({parent_status})"
