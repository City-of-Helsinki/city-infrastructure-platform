from django.db import models
from django.utils.translation import gettext_lazy as _


class RevertStreetScanImportRun(models.Model):
    """Tracks a single execution of the revert_import_streetscan_signs_v2 management command.

    Each live or dry-run invocation writes one row here, recording counds, skip/warning/error details."""

    id = models.BigAutoField(primary_key=True)
    started_at = models.DateTimeField(
        _("Started at"), auto_now_add=True, help_text=_("Timestamp when the import run was started")
    )
    completed_at = models.DateTimeField(
        _("Completed at"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the import run finished."),
    )
    dry_run = models.BooleanField(
        _("Dry run"),
        default=False,
        help_text=_("True if the run was executed with --dry-run (no DB writes performed)."),
    )
    file_path = models.CharField(
        _("Revert file"),
        max_length=512,
        help_text=_("Path or name of the JSON file containing the operations to be reverted."),
    )
    ids_param = models.JSONField(blank=False, null=False, help_text=_("--ids parameter of the run."))
    models_param = models.JSONField(blank=False, null=False, help_text=_("--models parameter of the run."))
    execution_log = models.TextField(
        blank=False, null=False, help_text=_("Detailed log information of the command run.")
    )
