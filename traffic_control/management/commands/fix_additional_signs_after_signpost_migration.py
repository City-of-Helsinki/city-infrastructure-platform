"""
Management command to fix AdditionalSign objects that were incorrectly soft-deleted
during a previous run of move_traffic_signs_to_signposts.

When move_traffic_signs_to_signposts ran before the signpost_plan/signpost_real FK
fields were added to AdditionalSign models, it soft-deleted TrafficSign objects without
first re-parenting their AdditionalSign children. This caused the AdditionalSigns to be
cascade-soft-deleted alongside the TrafficSign.

This command uses SignpostMigrationRun records to identify affected AdditionalSign objects
and restores them, re-pointing their parent FK to the appropriate SignpostPlan/SignpostReal.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional, Type

from auditlog.context import set_actor
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.db.models import QuerySet

from traffic_control.models.additional_sign import AdditionalSignPlan, AdditionalSignReal
from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)
from users.utils import get_system_user

logger = logging.getLogger(__name__)

# Default tolerance window: additional signs deleted within this many seconds of the
# migration run's completed_at are considered cascade victims rather than intentional deletions.
DEFAULT_TIME_TOLERANCE_SECONDS = 120


@dataclass
class MigrationTypeConfig:
    """Configuration that captures all Plan/Real differences for the fix logic.

    Attributes:
        label: Human-readable label used in output messages.
        record_model: The migration record model to query (Plan or Real).
        record_fk_field: FK field name on the record pointing to the new signpost object.
        additional_sign_model: The AdditionalSign model to restore (Plan or Real).
        parent_fk_field: The field name on the AdditionalSign holding the old TrafficSign FK.
        signpost_fk_field: The field name on the AdditionalSign for the new signpost FK.
    """

    label: str
    record_model: Type[models.Model]
    record_fk_field: str
    additional_sign_model: Type[models.Model]
    parent_fk_field: str
    signpost_fk_field: str


PLAN_CONFIG = MigrationTypeConfig(
    label="📋 AdditionalSignPlan",
    record_model=SignpostMigrationPlanRecord,
    record_fk_field="new_signpost_plan",
    additional_sign_model=AdditionalSignPlan,
    parent_fk_field="parent_id",
    signpost_fk_field="signpost_plan",
)

REAL_CONFIG = MigrationTypeConfig(
    label="📍 AdditionalSignReal",
    record_model=SignpostMigrationRealRecord,
    record_fk_field="new_signpost_real",
    additional_sign_model=AdditionalSignReal,
    parent_fk_field="parent_id",
    signpost_fk_field="signpost_real",
)


class Command(BaseCommand):
    """Restore AdditionalSign objects cascade-deleted by a previous signpost migration run."""

    help = (
        "Restore AdditionalSign objects that were cascade-soft-deleted during a previous "
        "move_traffic_signs_to_signposts run and re-parent them to the new SignpostPlan/SignpostReal."
    )

    def add_arguments(self, parser) -> None:
        """Add command arguments.

        Args:
            parser: The argument parser.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be restored without making any changes.",
        )
        parser.add_argument(
            "--migration-run-id",
            type=int,
            default=None,
            help=(
                "ID of a specific SignpostMigrationRun to fix. "
                "Defaults to all successful, non-dry-run runs that used soft-delete."
            ),
        )
        parser.add_argument(
            "--time-tolerance-seconds",
            type=int,
            default=DEFAULT_TIME_TOLERANCE_SECONDS,
            help=(
                "Only restore AdditionalSign objects whose deleted_at timestamp falls within "
                "this many seconds of the migration run's completed_at. "
                f"Default: {DEFAULT_TIME_TOLERANCE_SECONDS}s."
            ),
        )

    def handle(self, *args, **options) -> None:
        """Execute the command.

        Args:
            *args: Positional arguments.
            **options: Command options from the argument parser.
        """
        with set_actor(get_system_user()):
            dry_run: bool = options["dry_run"]
            migration_run_id: Optional[int] = options["migration_run_id"]
            tolerance_seconds: int = options["time_tolerance_seconds"]

            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN MODE — no changes will be made"))

            runs = self._get_migration_runs(migration_run_id)
            if not runs.exists():
                self.stdout.write(self.style.WARNING("No eligible migration runs found."))
                return

            totals = {"plans_restored": 0, "reals_restored": 0}

            for run in runs:
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"Processing: {run}")
                totals["plans_restored"] += self._fix_for_type(run, PLAN_CONFIG, tolerance_seconds, dry_run)
                totals["reals_restored"] += self._fix_for_type(run, REAL_CONFIG, tolerance_seconds, dry_run)

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(self.style.SUCCESS("✅ Fix complete"))
            self.stdout.write(f"  AdditionalSignPlan  — restored: {totals['plans_restored']}")
            self.stdout.write(f"  AdditionalSignReal  — restored: {totals['reals_restored']}")
            if dry_run:
                self.stdout.write(self.style.WARNING("(DRY RUN — nothing was actually changed)"))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_migration_runs(self, migration_run_id: Optional[int]) -> QuerySet:
        """Return the SignpostMigrationRun queryset to process.

        Args:
            migration_run_id: Specific run ID, or None for all eligible runs.

        Returns:
            QuerySet of SignpostMigrationRun objects.
        """
        qs = SignpostMigrationRun.objects.filter(
            success=True,
            dry_run=False,
            hard_delete=False,
        ).order_by("started_at")

        if migration_run_id is not None:
            qs = qs.filter(id=migration_run_id)

        return qs

    def _fix_for_type(
        self,
        run: SignpostMigrationRun,
        config: MigrationTypeConfig,
        tolerance_seconds: int,
        dry_run: bool,
    ) -> int:
        """Restore cascade-deleted AdditionalSign objects of one type for a migration run.

        Args:
            run: The SignpostMigrationRun to process.
            config: Type-specific configuration (plan or real).
            tolerance_seconds: Time window (seconds) for identifying cascade victims.
            dry_run: If True, report only without writing.

        Returns:
            int: Count of restored AdditionalSign objects.
        """
        self.stdout.write(f"\n  {config.label}:")
        records = config.record_model.objects.filter(
            migration_run=run,
            **{f"{config.record_fk_field}__isnull": False},
        ).select_related(config.record_fk_field)

        restored = 0

        for record in records:
            original_id = record.original_id
            new_signpost_obj = getattr(record, config.record_fk_field)
            victims = self._find_victims(original_id, run, config, tolerance_seconds)

            for victim in victims:
                self._restore_victim(victim, new_signpost_obj, config, dry_run)
                restored += 1
                action = "[DRY RUN] Would restore" if dry_run else "✓ Restored"
                self.stdout.write(
                    f"    {action} {config.additional_sign_model.__name__} {victim.id}"
                    f" → {new_signpost_obj.__class__.__name__} {new_signpost_obj.id}"
                )

        self.stdout.write(f"    Restored: {restored}")
        return restored

    def _find_victims(
        self,
        original_id: Any,
        run: SignpostMigrationRun,
        config: MigrationTypeConfig,
        tolerance_seconds: int,
    ) -> QuerySet:
        """Find AdditionalSign objects cascade-deleted by a traffic sign migration.

        Uses the parent_id UUID column to match the original traffic sign even if its
        row has since been hard-deleted. Filters by a deleted_at time window around the
        run's completed_at to avoid restoring unrelated manual deletions.

        Args:
            original_id: UUID of the original TrafficSign (Plan or Real).
            run: The migration run that caused the cascade.
            config: Type-specific configuration.
            tolerance_seconds: Tolerance window in seconds.

        Returns:
            QuerySet of candidate victim AdditionalSign objects.
        """
        if run.completed_at is None:
            return config.additional_sign_model.objects.none()

        window_start = run.completed_at - timedelta(seconds=tolerance_seconds)
        window_end = run.completed_at + timedelta(seconds=tolerance_seconds)

        return config.additional_sign_model.objects.filter(
            **{
                config.parent_fk_field: original_id,
                "is_active": False,
                f"{config.signpost_fk_field}__isnull": True,
                "deleted_at__gte": window_start,
                "deleted_at__lte": window_end,
            }
        )

    @transaction.atomic
    def _restore_victim(
        self,
        victim: models.Model,
        new_signpost_obj: models.Model,
        config: MigrationTypeConfig,
        dry_run: bool,
    ) -> None:
        """Restore a single soft-deleted AdditionalSign and re-parent to the new signpost object.

        Args:
            victim: The soft-deleted AdditionalSign instance to restore.
            new_signpost_obj: The SignpostPlan or SignpostReal to set as the new parent.
            config: Type-specific configuration.
            dry_run: If True, return without saving.
        """
        if dry_run:
            return

        victim.is_active = True
        victim.deleted_at = None
        victim.deleted_by = None
        victim.updated_by = get_system_user()
        victim.parent = None
        setattr(victim, config.signpost_fk_field, new_signpost_obj)
        victim.save(update_fields=["is_active", "deleted_at", "deleted_by", "parent", config.signpost_fk_field])
