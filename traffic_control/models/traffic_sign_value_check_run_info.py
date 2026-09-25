import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class TrafficSignValueCheckRunInfo(models.Model):
    """Tracks a run of the check_traffic_sign_real_values management command.

    One row is written per run, also when nothing was fixed, so that there is a record of what
    was checked and what was found. `database_update` tells whether the run actually changed
    any traffic sign reals, which separates a dry run from a real fix run.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_time = models.DateTimeField(_("Start time"), help_text=_("Timestamp when the run was started."))
    end_time = models.DateTimeField(_("End time"), help_text=_("Timestamp when the run finished."))
    checked_codes = models.JSONField(
        _("Checked codes"),
        blank=False,
        null=True,
        help_text=_("Device type codes that were included in the run."),
    )
    problems = models.JSONField(
        _("Problems"),
        blank=False,
        null=True,
        help_text=_("Value problems that were found, including what was done about each of them."),
    )
    checked_count = models.PositiveIntegerField(
        _("Checked count"), default=0, help_text=_("Number of traffic sign reals that were checked.")
    )
    problem_count = models.PositiveIntegerField(
        _("Problem count"), default=0, help_text=_("Number of traffic sign reals that had a value problem.")
    )
    fixed_count = models.PositiveIntegerField(
        _("Fixed count"),
        default=0,
        help_text=_("Number of problems that were corrected, or that would be corrected on a dry run."),
    )
    skipped_fix_count = models.PositiveIntegerField(
        _("Skipped fix count"),
        default=0,
        help_text=_("Number of problems that could not be corrected."),
    )
    database_update = models.BooleanField(
        _("Database updated"),
        default=False,
        help_text=_("Whether the run actually updated traffic sign reals."),
    )

    class Meta:
        verbose_name = _("Traffic sign value check run info")
        verbose_name_plural = _("Traffic sign value check run infos")
        ordering = ("-start_time",)

    def __str__(self) -> str:
        """Describe the run.

        Returns:
            str: Start time of the run and the number of problems that were found.
        """
        return f"{self.start_time}: {self.problem_count} problem(s) in {self.checked_count} sign(s)"
