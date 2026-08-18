from dataclasses import dataclass, field as dataclass_field
from typing import Any, Optional
from uuid import UUID

from auditlog.context import set_actor
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.models import (
    AdditionalSignReal,
    LinkAdditionalSignParentsRunInfo,
    SignpostReal,
    TrafficSignReal,
)
from users.utils import get_system_user

PARENT_FIELD = "parent"
SIGNPOST_FIELD = "signpost_real"


@dataclass(frozen=True)
class ParentLink:
    """Resolved parent for an AdditionalSignReal.

    Attributes:
        field (str): Name of the AdditionalSignReal field to set, either "parent" or "signpost_real".
        target_id (UUID): Primary key of the TrafficSignReal or SignpostReal to link to.
    """

    field: str
    target_id: UUID


@dataclass
class LinkStats:
    """Mutable statistics collected while resolving parents.

    Attributes:
        skipped_no_match (int): Number of additional signs with no matching active device on the same mount.
        skipped_no_active_above (int): Number of additional signs where no active device is positioned above.
        linked_records (list[dict]): Records describing the resolved links.
        skipped_records (list[dict]): Records describing the skipped additional signs.
    """

    skipped_no_match: int = 0
    skipped_no_active_above: int = 0
    linked_records: list[dict] = dataclass_field(default_factory=list)
    skipped_records: list[dict] = dataclass_field(default_factory=list)


class Command(TrackableCommand):
    help = (
        "Link additional sign parents by mount. Ticket machines are not included. "
        "Searches for an active traffic sign that has the same mount as the additional sign and links them together. "
        "If no traffic sign is found, an active signpost real with the same mount is used instead and set as "
        "the additional sign's signpost_real. When several active devices share a mount, the one positioned "
        "above the additional sign with the closest z-coordinate is selected. If no active devices are "
        "positioned above the additional sign, it is skipped."
    )

    def add_arguments(self, parser):
        """Add arguments specific to this command.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help=("Preview the additional signs that would be linked without making any database changes. "),
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the management command.

        Args:
            args (Any): Positional arguments.
            options (Any): Command options including dry_run flag.
        """
        system_user = get_system_user()
        with set_actor(system_user):
            dry_run: bool = options.get("dry_run", False)

            # Create run info record
            run_info = LinkAdditionalSignParentsRunInfo.objects.create(
                started_at=timezone.now(),
                dry_run=dry_run,
            )

            self.stdout.write("=" * 70)
            self.stdout.write("Link Additional Sign Parents by Mount")
            self.stdout.write("=" * 70)

            if dry_run:
                self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be made."))
                self.stdout.write("")

            new_parents_by_ads: dict[UUID, ParentLink] = self._get_new_parents(run_info)

            if dry_run:
                self._report_dry_run(new_parents_by_ads)
            else:
                self.do_parent_updates(new_parents_by_ads)

            # Update run info with end time and final stats
            run_info.completed_at = timezone.now()
            run_info.successfully_linked = len(new_parents_by_ads)
            run_info.save()

            self.stdout.write("")
            self.stdout.write(f"Run info saved with ID: {run_info.id}")
            self.stdout.write("=" * 70)

    def _report_dry_run(self, new_parents_by_ads: dict[UUID, ParentLink]) -> None:
        """Print a summary of the links that would be created in a non dry-run.

        Args:
            new_parents_by_ads (dict[UUID, ParentLink]): Mapping of AdditionalSignReal.id to its resolved parent link.
        """
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(f"Total AdditionalSignReal instances that would be linked: {len(new_parents_by_ads)}")
        )

        if not new_parents_by_ads:
            return

        self.stdout.write("")
        self.stdout.write("Sample records that would be updated (first 5):")
        for idx, (ads_id, link) in enumerate(list(new_parents_by_ads.items())[:5], 1):
            target_model = "TrafficSignReal" if link.field == PARENT_FIELD else "SignpostReal"
            self.stdout.write(f"  {idx}. AdditionalSignReal {ads_id} -> {target_model} {link.target_id}")

    def _get_new_parents(self, run_info: LinkAdditionalSignParentsRunInfo) -> dict[UUID, ParentLink]:
        """Get mapping of AdditionalSignReal IDs to their new parent links.

        A TrafficSignReal sharing the mount is preferred. When none exists, a SignpostReal sharing the mount is
        used instead and it is linked through the signpost_real field. Within either model, active devices are
        preferred over soft deleted ones and the latest created device wins.

        Args:
            run_info (LinkAdditionalSignParentsRunInfo): Run info record to update with statistics

        Returns:
            dict[UUID, ParentLink]: Dictionary mapping AdditionalSignReal.id to its resolved parent link.
        """
        # Get all additional signs that need parents
        additional_signs_qs = (
            AdditionalSignReal.objects.filter(
                parent__isnull=True,
                signpost_real__isnull=True,
                mount_real__isnull=False,
            )
            .exclude(device_type__code__in=TICKET_MACHINE_CODES)
            .select_related("mount_real")
        )

        parent_mapping: dict[UUID, ParentLink] = {}
        stats = LinkStats()

        run_info.total_candidates = additional_signs_qs.count()

        for ads in additional_signs_qs:
            link = self._resolve_link(ads, stats)
            if link is None:
                continue

            parent_mapping[ads.id] = link
            stats.linked_records.append(
                {
                    "additional_sign_real_id": str(ads.id),
                    "traffic_sign_real_id": str(link.target_id) if link.field == PARENT_FIELD else None,
                    "signpost_real_id": str(link.target_id) if link.field == SIGNPOST_FIELD else None,
                    "mount_real_id": str(ads.mount_real_id),
                }
            )

        # Update run info with statistics
        run_info.skipped_no_match = stats.skipped_no_match
        run_info.skipped_no_active_above = stats.skipped_no_active_above
        run_info.linked_records = stats.linked_records if stats.linked_records else None
        run_info.skipped_records = stats.skipped_records if stats.skipped_records else None
        run_info.save()

        self._report_statistics(len(parent_mapping), stats)

        return parent_mapping

    def _resolve_link(self, ads: AdditionalSignReal, stats: LinkStats) -> Optional[ParentLink]:
        """Resolve the parent for a single additional sign based on its mount.

        Args:
            ads (AdditionalSignReal): Additional sign to resolve a parent for.
            stats (LinkStats): Statistics container that is updated in place.

        Returns:
            Optional[ParentLink]: The resolved parent link or None when no candidate shares the mount.
        """
        ads_z = ads.location.z

        traffic_signs = TrafficSignReal.objects.active().filter(mount_real=ads.mount_real).order_by("-created_at")
        if traffic_signs.exists():
            traffic_sign = self._select_best_candidate(traffic_signs, ads, "TrafficSignReal", stats)
            if traffic_sign:
                return ParentLink(PARENT_FIELD, traffic_sign.id)

        self.stdout.write(
            self.style.WARNING(
                f"No active TrafficSignReal above AdditionalSignReal {ads.id} with mount_real {ads.mount_real_id}"
            )
        )

        signposts = SignpostReal.objects.active().filter(mount_real=ads.mount_real).order_by("-created_at")
        if signposts.exists():
            signpost = self._select_best_candidate(signposts, ads, "SignpostReal", stats)
            if signpost:
                return ParentLink(SIGNPOST_FIELD, signpost.id)

        # Determine skip reason based on whether any active devices were found
        if not traffic_signs.exists() and not signposts.exists():
            stats.skipped_no_match += 1
            reason = "no_matching_active_traffic_sign_or_signpost"
            self.stdout.write(
                self.style.WARNING(
                    f"No active SignpostReal found either for AdditionalSignReal {ads.id} "
                    f"with mount_real {ads.mount_real_id}"
                )
            )
        else:
            stats.skipped_no_active_above += 1
            reason = "no_active_candidates_above"
            self.stdout.write(
                self.style.WARNING(
                    f"No active candidates positioned above AdditionalSignReal {ads.id} "
                    f"(z={ads_z:.2f}) with mount_real {ads.mount_real_id}"
                )
            )

        stats.skipped_records.append(
            {
                "additional_sign_real_id": str(ads.id),
                "mount_real_id": str(ads.mount_real_id),
                "reason": reason,
            }
        )
        return None

    def _select_best_candidate(
        self, queryset: QuerySet, ads: AdditionalSignReal, model_name: str, stats: LinkStats
    ) -> Optional[any]:
        """Select the best candidate positioned above the additional sign with minimum z-difference.

        Only active candidates are considered (queryset should already be filtered with .active()).
        Selects the candidate with the smallest z-difference where candidate.z > ads.z.
        If multiple candidates have the same minimum z-difference, the latest created one is selected.

        Args:
            queryset (QuerySet): Active candidates sharing the same mount.
            ads (AdditionalSignReal): The additional sign being processed.
            model_name (str): Human readable name of the candidate model, used in output messages.
            stats (LinkStats): Statistics container that is updated in place (currently unused).

        Returns:
            Optional[Model]: The preferred candidate instance, or None if no candidate is above the additional sign.
        """
        selected = None
        min_z_diff = None
        ads_z = ads.location.z

        for candidate in queryset:
            diff_z = candidate.location.z - ads_z
            # Select candidate with minimum positive z-difference (above the additional sign)
            # Assumes that incoming queryset is ordered by -created_at, so latest created is preferred in case of tie
            if diff_z > 0:
                if min_z_diff is None or diff_z < min_z_diff:
                    selected = candidate
                    min_z_diff = diff_z

        if selected:
            self.stdout.write(
                f"Selected {model_name} {selected.id} for AdditionalSignReal {ads.id} "
                f"on mount {ads.mount_real_id} (z={selected.location.z:.2f}, z-diff={min_z_diff:.2f})"
            )

        return selected

    def _report_statistics(self, linked_count: int, stats: LinkStats) -> None:
        """Write the resolution statistics to stdout.

        Args:
            linked_count (int): Number of additional signs that got a parent resolved.
            stats (LinkStats): Collected statistics.
        """
        self.stdout.write(f"Found {linked_count} AdditionalSignReal instances to link.")
        if stats.skipped_no_match > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {stats.skipped_no_match} (no matching active TrafficSignReal or SignpostReal)."
                )
            )
        if stats.skipped_no_active_above > 0:
            self.stdout.write(
                self.style.WARNING(f"Skipped {stats.skipped_no_active_above} (no active candidates positioned above).")
            )

    def do_parent_updates(self, new_parents_by_ads: dict[UUID, ParentLink]) -> None:
        """Update parent and signpost_real fields for AdditionalSignReal instances.

        Args:
            new_parents_by_ads (dict[UUID, ParentLink]): Mapping of AdditionalSignReal.id to its resolved parent link.
        """
        if not new_parents_by_ads:
            self.stdout.write(self.style.WARNING("No AdditionalSignReal instances to update."))
            return

        system_user = get_system_user()

        # Fetch all AdditionalSignReal instances to update
        ads_instances = AdditionalSignReal.objects.filter(id__in=new_parents_by_ads.keys())

        # Update parent / signpost_real and updated_by fields
        updated_instances = []
        for ads in ads_instances:
            link = new_parents_by_ads[ads.id]
            setattr(ads, f"{link.field}_id", link.target_id)
            ads.updated_by = system_user
            updated_instances.append(ads)

        # Use bulk_update for better performance
        AdditionalSignReal.objects.bulk_update(
            updated_instances,
            fields=[PARENT_FIELD, SIGNPOST_FIELD, "updated_by"],
            batch_size=500,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully linked {len(updated_instances)} AdditionalSignReal instances to their parents."
            )
        )
