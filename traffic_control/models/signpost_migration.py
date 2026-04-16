"""
Models for tracking traffic sign to signpost migration.

These models record the execution and details of migrating traffic sign objects
with specific device type codes from TrafficSignPlan/TrafficSignReal tables
to SignpostPlan/SignpostReal tables.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from traffic_control.models.migration_common import BaseFieldTrackingMixin
from traffic_control.models.signpost import SignpostPlan, SignpostReal
from traffic_control.models.traffic_sign import TrafficSignPlan, TrafficSignReal

User = get_user_model()


class SignpostMigrationRun(models.Model):
    """
    Tracks a single execution of the move_traffic_signs_to_signposts command.

    Records migration statistics and configuration for auditing purposes.
    """

    id = models.BigAutoField(primary_key=True)
    executed_by = models.ForeignKey(
        User,
        verbose_name=_("Executed by"),
        on_delete=models.PROTECT,
        help_text=_("User who executed the migration command."),
    )
    started_at = models.DateTimeField(
        _("Started at"),
        auto_now_add=True,
        help_text=_("Timestamp when the migration was started."),
    )
    completed_at = models.DateTimeField(
        _("Completed at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the migration was completed (successfully or with error)."),
    )
    dry_run = models.BooleanField(
        _("Dry run"),
        default=False,
        help_text=_("Whether this was a dry run (no actual changes made)."),
    )
    hard_delete = models.BooleanField(
        _("Hard delete"),
        default=False,
        help_text=_("Whether original objects were permanently deleted (True) or soft-deleted (False)."),
    )
    success = models.BooleanField(
        _("Success"),
        null=True,
        blank=True,
        help_text=_("Whether the migration completed successfully."),
    )
    error_message = models.TextField(
        _("Error message"),
        blank=True,
        default="",
        help_text=_("Error message if migration failed."),
    )

    # Statistics
    plans_processed = models.IntegerField(_("Plans processed"), default=0)
    plans_migrated = models.IntegerField(_("Plans migrated"), default=0)
    reals_processed = models.IntegerField(_("Reals processed"), default=0)
    reals_migrated = models.IntegerField(_("Reals migrated"), default=0)
    plan_files_migrated = models.IntegerField(_("Plan files migrated"), default=0)
    real_files_migrated = models.IntegerField(_("Real files migrated"), default=0)
    device_types_updated = models.IntegerField(_("Device types updated"), default=0)

    # Lost field value tracking
    lost_field_values = models.JSONField(
        _("Lost field values"),
        default=dict,
        blank=True,
        help_text=_(
            "Dictionary of field names to sets of unique values that were lost during migration. "
            "Example: {'surface_class': ['FLAT', 'CONVEX'], 'affect_area': ['had_polygon'], "
            "'peak_fastened': ['True', 'False']}"
        ),
    )

    class Meta:
        db_table = "signpost_migration_run"
        verbose_name = _("Signpost Migration Run")
        verbose_name_plural = _("Signpost Migration Runs")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        if self.success:
            status = "Success"
        elif self.success is False:
            status = "Failed"
        else:
            status = "In Progress"
        mode = "DRY RUN" if self.dry_run else "REAL"
        return f"Signpost Migration {self.id} - {mode} - {status} ({self.started_at})"


class SignpostMigrationPlanRecord(BaseFieldTrackingMixin):
    """
    Detailed record of a single TrafficSignPlan migration to SignpostPlan.

    Tracks original and new IDs, field presence, and lost data for auditing.
    """

    id = models.BigAutoField(primary_key=True)
    migration_run = models.ForeignKey(
        SignpostMigrationRun,
        verbose_name=_("Migration run"),
        on_delete=models.CASCADE,
        related_name="plan_records",
        help_text=_("The migration run this record belongs to."),
    )

    # Object references (nullable to support dry-run and deleted objects)
    original_traffic_sign_plan = models.ForeignKey(
        TrafficSignPlan,
        verbose_name=_("Original TrafficSignPlan"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signpost_migration_records",
    )
    new_signpost_plan = models.ForeignKey(
        SignpostPlan,
        verbose_name=_("New SignpostPlan"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_source_records",
    )

    # IDs for permanent tracking (even after deletion)
    original_id = models.UUIDField(_("Original ID"), help_text=_("ID of the original TrafficSignPlan."))
    new_id = models.UUIDField(
        _("New ID"),
        null=True,
        blank=True,
        help_text=_("ID of the new SignpostPlan (null for dry-run)."),
    )

    # Device type
    device_type_code = models.CharField(
        _("Device type code"),
        max_length=32,
        help_text=_("Code of the device type being migrated."),
    )

    # Plan-specific field tracking
    had_mount_plan = models.BooleanField(_("Had mount_plan"), default=False)
    had_plan = models.BooleanField(_("Had plan"), default=False)

    # Lost fields (fields that exist in TrafficSign but not in Signpost)
    lost_surface_class = models.CharField(
        _("Lost surface_class"),
        max_length=10,
        blank=True,
        help_text=_("Value of surface_class field that was lost."),
    )
    lost_peak_fastened = models.BooleanField(
        _("Lost peak_fastened"),
        default=False,
        help_text=_("Value of peak_fastened field that was lost."),
    )
    had_affect_area = models.BooleanField(
        _("Had affect_area"),
        default=False,
        help_text=_("Whether the original had an affect_area polygon."),
    )

    class Meta:
        db_table = "signpost_migration_plan_record"
        verbose_name = _("Signpost Migration Plan Record")
        verbose_name_plural = _("Signpost Migration Plan Records")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["migration_run", "device_type_code"]),
            models.Index(fields=["original_id"]),
            models.Index(fields=["new_id"]),
        ]

    def __str__(self) -> str:
        return f"Plan Migration: {self.device_type_code} {self.original_id} → {self.new_id}"


class SignpostMigrationRealRecord(BaseFieldTrackingMixin):
    """
    Detailed record of a single TrafficSignReal migration to SignpostReal.

    Tracks original and new IDs, field presence, plan mapping, and lost data for auditing.
    """

    id = models.BigAutoField(primary_key=True)
    migration_run = models.ForeignKey(
        SignpostMigrationRun,
        verbose_name=_("Migration run"),
        on_delete=models.CASCADE,
        related_name="real_records",
        help_text=_("The migration run this record belongs to."),
    )

    # Object references (nullable to support dry-run and deleted objects)
    original_traffic_sign_real = models.ForeignKey(
        TrafficSignReal,
        verbose_name=_("Original TrafficSignReal"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signpost_migration_records",
    )
    new_signpost_real = models.ForeignKey(
        SignpostReal,
        verbose_name=_("New SignpostReal"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="migration_source_records",
    )

    # IDs for permanent tracking (even after deletion)
    original_id = models.UUIDField(_("Original ID"), help_text=_("ID of the original TrafficSignReal."))
    new_id = models.UUIDField(
        _("New ID"),
        null=True,
        blank=True,
        help_text=_("ID of the new SignpostReal (null for dry-run)."),
    )

    # Device type
    device_type_code = models.CharField(
        _("Device type code"),
        max_length=32,
        help_text=_("Code of the device type being migrated."),
    )

    # Plan mapping
    plan_mapping_found = models.BooleanField(
        _("Plan mapping found"),
        default=False,
        help_text=_("Whether a corresponding SignpostPlan was found for the traffic_sign_plan reference."),
    )

    # Real-specific field tracking (not in TrafficSignPlan)
    had_mount_real = models.BooleanField(_("Had mount_real"), default=False)
    had_traffic_sign_plan = models.BooleanField(_("Had traffic_sign_plan"), default=False)
    had_legacy_code = models.BooleanField(_("Had legacy_code"), default=False)
    had_scanned_at = models.BooleanField(_("Had scanned_at"), default=False)
    had_manufacturer = models.BooleanField(_("Had manufacturer"), default=False)
    had_installation_status = models.BooleanField(_("Had installation_status"), default=False)
    had_installation_date = models.BooleanField(_("Had installation_date"), default=False)
    had_condition = models.BooleanField(_("Had condition"), default=False)

    # Lost fields (fields that exist in TrafficSignReal but not in SignpostReal)
    lost_surface_class = models.CharField(
        _("Lost surface_class"),
        max_length=10,
        blank=True,
        help_text=_("Value of surface_class field that was lost."),
    )
    lost_peak_fastened = models.BooleanField(
        _("Lost peak_fastened"),
        default=False,
        help_text=_("Value of peak_fastened field that was lost."),
    )
    lost_installation_id = models.CharField(
        _("Lost installation_id"),
        max_length=254,
        blank=True,
        help_text=_("Value of installation_id field that was lost."),
    )
    lost_installation_details = models.CharField(
        _("Lost installation_details"),
        max_length=254,
        blank=True,
        help_text=_("Value of installation_details field that was lost."),
    )
    lost_permit_decision_id = models.CharField(
        _("Lost permit_decision_id"),
        max_length=254,
        blank=True,
        help_text=_("Value of permit_decision_id field that was lost."),
    )
    lost_rfid = models.CharField(
        _("Lost rfid"),
        max_length=254,
        blank=True,
        help_text=_("Value of rfid field that was lost."),
    )
    lost_operation = models.CharField(
        _("Lost operation"),
        max_length=64,
        blank=True,
        help_text=_("Value of operation field that was lost."),
    )
    lost_attachment_url = models.URLField(
        _("Lost attachment_url"),
        max_length=500,
        blank=True,
        help_text=_("Value of attachment_url field that was lost."),
    )

    class Meta:
        db_table = "signpost_migration_real_record"
        verbose_name = _("Signpost Migration Real Record")
        verbose_name_plural = _("Signpost Migration Real Records")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["migration_run", "device_type_code"]),
            models.Index(fields=["original_id"]),
            models.Index(fields=["new_id"]),
        ]

    def __str__(self) -> str:
        return f"Real Migration: {self.device_type_code} {self.original_id} → {self.new_id}"
