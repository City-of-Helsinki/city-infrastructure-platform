from django.db import models
from django.utils.translation import gettext_lazy as _


class SearchOrphanFilesRunInfo(models.Model):
    """Tracks the latest execution of the search_orphan_files management command."""

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
    execution_log = models.TextField(
        blank=False, null=False, help_text=_("Detailed log information of the command run.")
    )
