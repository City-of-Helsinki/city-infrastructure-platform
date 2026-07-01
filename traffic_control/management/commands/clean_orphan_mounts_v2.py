"""Management command to clean orphan MountReal records from V2 StreetScan imports."""
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME, TrafficSignImporterV2
from traffic_control.models import MountReal


class Command(BaseCommand):
    """Hard-delete orphan MountReal records scoped to the V2 StreetScan import source.

    An orphan is a MountReal with source_name matching the V2 import source name
    that is not referenced by any TrafficSignReal, AdditionalSignReal, or SignpostReal
    with the same source_name.

    Use --dry-run to preview the mounts that would be deleted without making any
    database changes. Combine with --dry-run-detail to choose between a count summary
    (default) and a full list of UUIDs.
    """

    help = (
        "Hard-delete orphan MountReal records from StreetScan V2 imports. "
        "Use --dry-run to preview what would be deleted without making database changes."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help=(
                "Preview the orphan mounts that would be deleted without making any database changes. "
                "Use --dry-run-detail to control the level of detail shown."
            ),
        )
        parser.add_argument(
            "--dry-run-detail",
            choices=["count", "ids"],
            default="count",
            dest="dry_run_detail",
            help=(
                "Level of detail to display in dry-run mode. "
                "'count' (default) prints only the total number of orphan mounts; "
                "'ids' prints each orphan mount UUID on a separate line."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the orphan mount cleanup command.

        Args:
            *args: Positional arguments (unused).
            **options: Parsed command options.
        """
        dry_run: bool = options["dry_run"]
        dry_run_detail: str = options["dry_run_detail"]

        if dry_run:
            self._handle_dry_run(dry_run_detail)
            return

        self._handle_delete()

    def _handle_dry_run(self, detail: str) -> None:
        """Preview orphan mounts without making database changes.

        Args:
            detail (str): Level of detail to display — 'count' or 'ids'.
        """
        orphan_ids: set[UUID] = TrafficSignImporterV2.get_orphan_mount_ids()
        self.stdout.write(self.style.WARNING("DRY RUN — no database changes will be made"))

        if detail == "ids":
            self._print_orphan_ids(orphan_ids)
            return

        self.stdout.write(f"Orphan mounts that would be deleted: {len(orphan_ids)}")

    def _print_orphan_ids(self, orphan_ids: set[UUID]) -> None:
        """Print each orphan mount UUID to stdout.

        Args:
            orphan_ids (set[UUID]): Set of orphan MountReal primary keys.
        """
        self.stdout.write(f"Orphan mounts that would be deleted ({len(orphan_ids)}):")
        for mount_id in sorted(str(oid) for oid in orphan_ids):
            self.stdout.write(f"  {mount_id}")

    @transaction.atomic
    def _handle_delete(self) -> None:
        """Hard-delete all orphan mounts scoped to SOURCE_NAME and report the result.

        Returns:
            None
        """
        orphan_ids: set[UUID] = TrafficSignImporterV2.get_orphan_mount_ids()
        count: int = len(orphan_ids)

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orphan mounts found — nothing to delete."))
            return

        MountReal.objects.filter(id__in=orphan_ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} orphan mount(s) with source_name='{SOURCE_NAME}'."))
