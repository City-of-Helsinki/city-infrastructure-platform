from argparse import ArgumentParser
from typing import Any

from auditlog.context import set_actor
from django.db.models import Q, QuerySet

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.models import Plan
from traffic_control.services.plan import get_plan_decision_url
from users.utils import get_system_user


class Command(TrackableCommand):
    help = (
        "Populates Plan.decision_url based on Plan.diary_number. "
        "By default only plans with an empty decision_url are updated. "
        "Use --force to regenerate the decision_url for every plan that has a diary number."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command line arguments.

        Args:
            parser (ArgumentParser): Argument parser of the command.

        Returns:
            None
        """
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            default=False,
            help="Only print what would be updated, do not write to the database",
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            default=False,
            help="Regenerate decision_url also for plans that already have one",
        )

    def handle(
        self,
        *,
        dry_run: bool,
        force: bool,
        **_kwargs: Any,
    ) -> None:
        """Populate decision urls for existing plans.

        Args:
            dry_run (bool): Whether to only print the changes without writing them.
            force (bool): Whether to regenerate the decision url also for plans that already
                have one.
            **_kwargs: Remaining command options (unused).

        Returns:
            None
        """
        if dry_run:
            self.stdout.write(self.style.NOTICE("Doing dry run, not updating database"))

        user = get_system_user()
        updated_count = 0
        unchanged_count = 0

        with set_actor(user):
            for plan in self._get_plans(force):
                decision_url = get_plan_decision_url(plan.diary_number)
                if decision_url == (plan.decision_url or ""):
                    unchanged_count += 1
                    continue

                self.stdout.write(f"Plan {plan.pk} ({plan.diary_number}): {plan.decision_url!r} -> {decision_url!r}")
                if not dry_run:
                    plan.decision_url = decision_url
                    plan.updated_by = user
                    plan.save(update_fields=["decision_url", "updated_by"])
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} plans. Unchanged: {unchanged_count}"))

    @staticmethod
    def _get_plans(force: bool) -> QuerySet:
        """Get the plans that are candidates for a decision url update.

        Args:
            force (bool): When True, plans with an existing decision_url are included.

        Returns:
            QuerySet: Active plans having a diary number.
        """
        queryset = Plan.objects.active().exclude(Q(diary_number__isnull=True) | Q(diary_number=""))
        if not force:
            queryset = queryset.filter(Q(decision_url__isnull=True) | Q(decision_url=""))

        return queryset
