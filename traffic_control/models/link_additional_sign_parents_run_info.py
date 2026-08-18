import uuid

from django.db import models


class LinkAdditionalSignParentsRunInfo(models.Model):
    """Track execution runs of link_additional_sign_parents_by_mount management command.

    This model stores information about each run of the command including:
    - Start and completion times
    - Whether it was a dry-run
    - Which AdditionalSignReal instances were linked to which TrafficSignReal or SignpostReal parents
    - Statistics about the run (total processed, skipped, etc.)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    dry_run = models.BooleanField(default=False)
    total_candidates = models.IntegerField(
        default=0,
        help_text="Total AdditionalSignReal instances that were candidates for linking",
    )
    successfully_linked = models.IntegerField(
        default=0,
        help_text="Number of AdditionalSignReal instances successfully linked",
    )
    skipped_no_match = models.IntegerField(
        default=0,
        help_text="Number skipped due to no matching active TrafficSignReal or SignpostReal",
    )
    skipped_no_active_above = models.IntegerField(
        default=0,
        help_text="Number skipped because no active candidates were positioned above the additional sign",
    )
    linked_records = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "List of dicts with keys: additional_sign_real_id, traffic_sign_real_id, signpost_real_id, mount_real_id"
        ),
    )
    skipped_records = models.JSONField(
        blank=True,
        null=True,
        help_text=("List of dicts with keys: additional_sign_real_id, mount_real_id, reason"),
    )

    class Meta:
        db_table = "link_additional_sign_parents_run_info"
        verbose_name = "Link Additional Sign Parents Run Info"
        verbose_name_plural = "Link Additional Sign Parents Run Infos"
        ordering = ["-started_at"]

    def __str__(self):
        """Return string representation.

        Returns:
            str: String showing run time and dry-run status
        """
        dry_run_text = " (DRY-RUN)" if self.dry_run else ""
        return f"Run {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}{dry_run_text}"
