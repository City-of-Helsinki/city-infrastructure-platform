"""Model for tracking V2 StreetScan import runs."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from traffic_control.mixins.models import AbstractFileModel


class StreetScanImportRun(models.Model):
    """Tracks a single execution of the import_streetscan_signs_v2 management command.

    Each live or dry-run invocation writes one row here, recording counts,
    skip/warning/error details, and the revert data file attachment.
    The revert file (if any) is stored as a related StreetScanImportRevertFile record.
    """

    id = models.BigAutoField(primary_key=True)
    ran_at = models.DateTimeField(
        _("Ran at"),
        auto_now_add=True,
        help_text=_("Timestamp when the import run was started."),
    )
    is_dry_run = models.BooleanField(
        _("Dry run"),
        default=False,
        help_text=_("True if the run was executed with --dry-run (no DB writes performed)."),
    )
    mount_file = models.CharField(
        _("Mount file"),
        max_length=512,
        help_text=_("Path or name of the mount CSV file used for this run."),
    )
    sign_file = models.CharField(
        _("Sign file"),
        max_length=512,
        help_text=_("Path or name of the sign CSV file used for this run."),
    )

    # --- Per-object-type counters ---

    mounts_created = models.IntegerField(_("Mounts created"), default=0)
    mounts_updated = models.IntegerField(_("Mounts updated"), default=0)

    signs_created = models.IntegerField(_("Signs created"), default=0)
    signs_updated = models.IntegerField(_("Signs updated"), default=0)
    signs_deactivated = models.IntegerField(
        _("Signs deactivated"),
        default=0,
        help_text=_("TrafficSignReal records whose lifecycle was set to INACTIVE."),
    )

    signposts_created = models.IntegerField(_("Signposts created"), default=0)
    signposts_updated = models.IntegerField(_("Signposts updated"), default=0)
    signposts_deactivated = models.IntegerField(_("Signposts deactivated"), default=0)

    additional_signs_created = models.IntegerField(_("Additional signs created"), default=0)
    additional_signs_updated = models.IntegerField(_("Additional signs updated"), default=0)
    additional_signs_deactivated = models.IntegerField(_("Additional signs deactivated"), default=0)

    # --- Aggregate event counters ---

    skipped_count = models.IntegerField(
        _("Skipped count"),
        default=0,
        help_text=_("Total rows skipped due to invalid geometry, unreadable text, missing device type code, etc."),
    )
    warning_count = models.IntegerField(
        _("Warning count"),
        default=0,
        help_text=_(
            "Total warning-level events: imported without a mount, without a parent, "
            "traffic sign with ignored parent value, etc."
        ),
    )
    error_count = models.IntegerField(
        _("Error count"),
        default=0,
        help_text=_("Total error-level events (unexpected exceptions during the run)."),
    )

    # --- Timing ---

    preprocessing_duration_s = models.FloatField(
        _("Preprocessing duration (s)"),
        null=True,
        blank=True,
        help_text=_(
            "Seconds spent loading and enriching CSV rows and building all DB lookup maps "
            "before the first import phase began."
        ),
    )
    phase_durations = models.JSONField(
        _("Phase durations"),
        default=dict,
        help_text=_(
            "Nested dict of seconds spent in each phase: "
            "{object_type: {phase: duration_s}}. "
            "Populated progressively as phases complete."
        ),
    )

    # --- Detailed event log ---

    details = models.JSONField(
        _("Details"),
        default=list,
        help_text=_(
            "Full list of per-row skip, warning and error entries. "
            "Each entry has at minimum: level ('skip'/'warning'/'error'), source_id, reason."
        ),
    )

    # --- Processed source_id sets (used for resume logic) ---

    processed_mount_source_ids = models.JSONField(
        _("Processed mount source IDs"),
        default=list,
        help_text=_("List of MountReal source_ids successfully upserted in this run."),
    )
    processed_sign_source_ids = models.JSONField(
        _("Processed sign source IDs"),
        default=list,
        help_text=_("List of TrafficSignReal source_ids successfully upserted in this run."),
    )
    processed_signpost_source_ids = models.JSONField(
        _("Processed signpost source IDs"),
        default=list,
        help_text=_("List of SignpostReal source_ids successfully upserted in this run."),
    )
    processed_additional_sign_source_ids = models.JSONField(
        _("Processed additional sign source IDs"),
        default=list,
        help_text=_("List of AdditionalSignReal source_ids successfully upserted in this run."),
    )

    # --- Revert data file ---
    # Stored as a related StreetScanImportRevertFile (see below).
    # Access via: run.revert_files.first()

    class Meta:
        verbose_name = _("StreetScan import run")
        verbose_name_plural = _("StreetScan import runs")
        ordering = ["-ran_at"]

    def __str__(self) -> str:
        """Return a human-readable representation of this run.

        Returns:
            str: String with run id, date and dry-run flag.
        """
        dry = " [dry-run]" if self.is_dry_run else ""
        return f"StreetScanImportRun #{self.pk} — {self.ran_at:%Y-%m-%d %H:%M}{dry}"


class StreetScanImportRevertFile(AbstractFileModel):
    """Stores the JSONL revert data file for a single StreetScanImportRun.

    Each non-dry import run produces at most one revert file, but the FK allows
    multiple files per run if that ever becomes necessary (e.g. per-phase files).
    The file is uploaded to the configured DEFAULT_FILE_STORAGE backend so it can
    later be moved to blob storage without model changes.
    """

    file = models.FileField(
        _("File"),
        blank=False,
        null=False,
        upload_to="streetscan_import/revert/",
        help_text=_("JSONL file containing pre-update snapshots and created-object IDs for this run."),
    )
    import_run = models.ForeignKey(
        StreetScanImportRun,
        verbose_name=_("Import run"),
        on_delete=models.PROTECT,
        related_name="revert_files",
        help_text=_("The import run this revert file belongs to."),
    )

    class Meta:
        db_table = "streetscan_import_revert_file"
        verbose_name = _("StreetScan import revert file")
        verbose_name_plural = _("StreetScan import revert files")
