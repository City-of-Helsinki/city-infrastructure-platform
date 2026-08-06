from django.db import models
from django.utils.translation import gettext_lazy as _


class TrackedManagementCommand(models.Model):
    """
    Model to track usage information about management commands.

    Tracking the usage of some commands might help reveal whether some of them have gone without use for a very long
    time and are candidates for deletion from the codebase.
    """

    id = models.CharField(primary_key=True, max_length=201, editable=False)  # Formatted as 'app_name-command_name'
    app = models.CharField(max_length=100, editable=False)
    command = models.CharField(max_length=100, editable=False)
    comment = models.TextField(
        blank=True,
        null=False,
        help_text=_("Notes on tracking the command or clarifications about the command's purpose"),
    )
    tracking_started_at = models.DateTimeField(
        help_text=_("When was usage tracking for this command started"),
        editable=False,
        auto_now_add=True,
    )
    latest_executed_at = models.DateTimeField(
        help_text=_("When was this command last executed. Unknown if it happened before tracking started"),
        default=None,
        editable=False,
        null=True,
    )

    def __str__(self):
        return self.id

    class Meta:
        ordering = ["app", "command"]
