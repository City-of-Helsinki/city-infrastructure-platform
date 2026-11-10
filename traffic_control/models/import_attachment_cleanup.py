"""Models for tracking cleanup runs of stale import attachment batches."""
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from traffic_control.enums import ImportAttachmentCleanupStatus

User = get_user_model()


class ImportAttachmentCleanupRun(models.Model):
    """Tracks each execution of the stale import attachment cleanup command."""

    id = models.BigAutoField(primary_key=True)
    started_at = models.DateTimeField(
        _("Started at"),
        auto_now_add=True,
        help_text=_("Timestamp when the cleanup command started."),
    )
    completed_at = models.DateTimeField(
        _("Completed at"),
        blank=True,
        null=True,
        help_text=_("Timestamp when the cleanup command completed."),
    )
    executed_by = models.ForeignKey(
        User,
        verbose_name=_("Executed by"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("User who executed the cleanup command."),
    )
    dry_run = models.BooleanField(
        _("Dry run"),
        default=False,
        help_text=_("Whether this was a dry run (no files were deleted)."),
    )
    max_age_hours = models.IntegerField(
        _("Max age hours"),
        default=0,
        help_text=_("Staged batches older than this many hours were considered stale."),
    )
    discarded_batches_count = models.IntegerField(
        _("Batches discarded"),
        default=0,
        help_text=_("Number of stale batches discarded, or that would be discarded on a dry run."),
    )
    files_discarded = models.IntegerField(
        _("Files discarded"),
        default=0,
        help_text=_("Number of staged files discarded, or that would be discarded on a dry run."),
    )
    discarded_batches = models.JSONField(
        _("Discarded batches"),
        default=dict,
        blank=True,
        help_text=_(
            "Mapping of discarded batch id to the file names it contained. "
            "Example: {'<batch uuid>': ['first.txt', 'second.pdf']}"
        ),
    )
    error_message = models.TextField(
        _("Error message"),
        blank=True,
        default="",
        help_text=_("Error message if the cleanup failed."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ImportAttachmentCleanupStatus.choices,
        default=ImportAttachmentCleanupStatus.IN_PROGRESS,
        help_text=_("Outcome of the cleanup run."),
    )

    class Meta:
        db_table = "import_attachment_cleanup_run"
        verbose_name = _("Import Attachment Cleanup Run")
        verbose_name_plural = _("Import Attachment Cleanup Runs")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            str: Start time, status and mode of the run.
        """
        status = self.get_status_display()
        mode = "DRY RUN" if self.dry_run else "DELETE"

        return f"{self.started_at.strftime('%Y-%m-%d %H:%M:%S')} - {status} ({mode})"
