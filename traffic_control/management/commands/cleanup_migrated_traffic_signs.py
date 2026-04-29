"""
Management command to hard-delete traffic signs previously soft-deleted by migration commands.

Cleans up TrafficSignPlan and TrafficSignReal objects that were soft-deleted by:
- move_ticket_machines_to_additional_signs
- move_traffic_signs_to_signposts

Candidates are identified through the respective migration run records.
Supports --dry-run for safe previewing and --migration-run for partial cleanup.
"""
import logging
from typing import Optional, Type

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Model

from traffic_control.models.signpost_migration import SignpostMigrationPlanRecord, SignpostMigrationRealRecord
from traffic_control.models.ticket_machine_migration import (
    TicketMachineMigrationPlanRecord,
    TicketMachineMigrationRealRecord,
)
from traffic_control.models.traffic_sign import TrafficSignPlan, TrafficSignReal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Hard-delete traffic signs soft-deleted by the ticket-machine and signpost migration commands."""

    help = (
        "Hard-delete TrafficSignPlan/TrafficSignReal objects that were soft-deleted by "
        "move_ticket_machines_to_additional_signs or move_traffic_signs_to_signposts."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): The argument parser to add arguments to.

        Returns:
            None
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be deleted without making any changes.",
        )
        parser.add_argument(
            "--ticket-machine-run",
            type=int,
            metavar="RUN_ID",
            help="Limit cleanup to a specific TicketMachineMigrationRun ID.",
        )
        parser.add_argument(
            "--signpost-run",
            type=int,
            metavar="RUN_ID",
            help="Limit cleanup to a specific SignpostMigrationRun ID.",
        )

    def handle(self, *args, **options) -> None:
        """Execute the cleanup command.

        Args:
            *args: Positional arguments (unused).
            **options: Parsed command-line options.

        Returns:
            None
        """
        dry_run: bool = options["dry_run"]
        ticket_machine_run_id: Optional[int] = options["ticket_machine_run"]
        signpost_run_id: Optional[int] = options["signpost_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        plan_ids = self._collect_plan_ids(ticket_machine_run_id, signpost_run_id)
        real_ids = self._collect_real_ids(ticket_machine_run_id, signpost_run_id)

        plans_qs = TrafficSignPlan.objects.filter(id__in=plan_ids, is_active=False)
        reals_qs = TrafficSignReal.objects.filter(id__in=real_ids, is_active=False)

        plans_count = plans_qs.count()
        reals_count = reals_qs.count()

        self._report_candidates(plans_count, reals_count)

        if not dry_run:
            self._delete_objects(plans_qs, reals_qs)
            self._report_completion(plans_count, reals_count)
        else:
            self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No changes were made"))

    # ── Collection helpers ────────────────────────────────────────────────────

    def _collect_plan_ids(
        self,
        ticket_machine_run_id: Optional[int],
        signpost_run_id: Optional[int],
    ) -> set:
        """Collect TrafficSignPlan UUIDs eligible for hard-deletion.

        Args:
            ticket_machine_run_id (Optional[int]): Limit to a specific TicketMachineMigrationRun.
            signpost_run_id (Optional[int]): Limit to a specific SignpostMigrationRun.

        Returns:
            set: Set of UUIDs for eligible TrafficSignPlan objects.
        """
        ticket_ids = self._collect_ids_from_record_model(TicketMachineMigrationPlanRecord, ticket_machine_run_id)
        signpost_ids = self._collect_ids_from_record_model(SignpostMigrationPlanRecord, signpost_run_id)
        return ticket_ids | signpost_ids

    def _collect_real_ids(
        self,
        ticket_machine_run_id: Optional[int],
        signpost_run_id: Optional[int],
    ) -> set:
        """Collect TrafficSignReal UUIDs eligible for hard-deletion.

        Args:
            ticket_machine_run_id (Optional[int]): Limit to a specific TicketMachineMigrationRun.
            signpost_run_id (Optional[int]): Limit to a specific SignpostMigrationRun.

        Returns:
            set: Set of UUIDs for eligible TrafficSignReal objects.
        """
        ticket_ids = self._collect_ids_from_record_model(TicketMachineMigrationRealRecord, ticket_machine_run_id)
        signpost_ids = self._collect_ids_from_record_model(SignpostMigrationRealRecord, signpost_run_id)
        return ticket_ids | signpost_ids

    # ── Per-source ID collectors ──────────────────────────────────────────────

    def _collect_ids_from_record_model(self, model: Type[Model], run_id: Optional[int]) -> set:
        """Return original_ids from a migration record model for completed soft-delete runs.

        Args:
            model (Type[Model]): A migration record model class with a ``migration_run`` FK
                and ``original_id`` / ``new_id`` fields.
            run_id (Optional[int]): Specific migration run ID to filter by, or None for all runs.

        Returns:
            set: Set of UUIDs eligible for hard-deletion.
        """
        qs = model.objects.filter(
            migration_run__dry_run=False,
            migration_run__hard_delete=False,
            migration_run__success=True,
            new_id__isnull=False,
        )
        if run_id is not None:
            qs = qs.filter(migration_run_id=run_id)
        return set(qs.values_list("original_id", flat=True))

    # ── Output helpers ────────────────────────────────────────────────────────

    def _report_candidates(self, plans_count: int, reals_count: int) -> None:
        """Write candidate counts to stdout.

        Args:
            plans_count (int): Number of TrafficSignPlan objects to delete.
            reals_count (int): Number of TrafficSignReal objects to delete.

        Returns:
            None
        """
        self.stdout.write(f"\nFound {plans_count} TrafficSignPlan object(s) eligible for hard-deletion")
        self.stdout.write(f"Found {reals_count} TrafficSignReal object(s) eligible for hard-deletion")

    def _delete_objects(self, plans_qs, reals_qs) -> None:
        """Hard-delete the supplied querysets.

        Args:
            plans_qs: QuerySet of TrafficSignPlan objects to delete.
            reals_qs: QuerySet of TrafficSignReal objects to delete.

        Returns:
            None
        """
        deleted_plans, _ = plans_qs.delete()
        logger.info("Hard-deleted %d TrafficSignPlan objects", deleted_plans)

        deleted_reals, _ = reals_qs.delete()
        logger.info("Hard-deleted %d TrafficSignReal objects", deleted_reals)

    def _report_completion(self, plans_count: int, reals_count: int) -> None:
        """Write completion summary to stdout.

        Args:
            plans_count (int): Number of TrafficSignPlan objects deleted.
            reals_count (int): Number of TrafficSignReal objects deleted.

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS(f"\n✓ Hard-deleted {plans_count} TrafficSignPlan object(s)"))
        self.stdout.write(self.style.SUCCESS(f"✓ Hard-deleted {reals_count} TrafficSignReal object(s)"))
        self.stdout.write(self.style.SUCCESS("\n✓ Cleanup completed successfully!"))
