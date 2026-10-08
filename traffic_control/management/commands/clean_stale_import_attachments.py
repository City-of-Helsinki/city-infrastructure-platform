"""Management command for removing abandoned import attachment batches from the staging area."""

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from traffic_control.services.import_attachments import discard_stale_batches

DEFAULT_MAX_AGE_HOURS = 24


class Command(BaseCommand):
    help = (
        "Delete attachment files that were staged for an admin import but never used, for example because the "
        "import was abandoned after the preview step."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Register the command's arguments.

        Args:
            parser (CommandParser): Parser to register the arguments on.

        Returns:
            None
        """
        parser.add_argument(
            "--max-age-hours",
            type=int,
            default=DEFAULT_MAX_AGE_HOURS,
            help=f"Delete staged batches older than this many hours. Defaults to {DEFAULT_MAX_AGE_HOURS}.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Discard staged attachment batches older than the given age.

        Args:
            *args (Any): Positional arguments.
            **options (Any): Parsed command options.

        Returns:
            None
        """
        max_age = timedelta(hours=options["max_age_hours"])
        discarded = discard_stale_batches(max_age)

        if not discarded:
            self.stdout.write("No stale import attachment batches found.")
            return

        for batch_id in discarded:
            self.stdout.write(f"Discarded import attachment batch {batch_id}")
        self.stdout.write(self.style.SUCCESS(f"Discarded {len(discarded)} stale import attachment batch(es)."))
