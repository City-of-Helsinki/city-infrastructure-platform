"""
Management command to move ticket machines from traffic_sign tables to additional_sign tables.

This command migrates ticket machine objects (device type codes H20.91, H20.92, H20.93, 8591, 8592, 8593)
from TrafficSignReal/TrafficSignPlan to AdditionalSignReal/AdditionalSignPlan.
"""
import logging
from typing import Any, Dict, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from traffic_control.analyze_utils.traffic_sign_data import TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models.additional_sign import (
    AdditionalSignPlan,
    AdditionalSignPlanFile,
    AdditionalSignReal,
    AdditionalSignRealFile,
    Color,
)
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.models.ticket_machine_migration import (
    TicketMachineMigrationPlanRecord,
    TicketMachineMigrationRealRecord,
    TicketMachineMigrationRun,
)
from traffic_control.models.traffic_sign import (
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)
from users.utils import get_system_user

logger = logging.getLogger(__name__)

PARENT_SIGN_CODES = ["E2", "521"]


class Command(BaseCommand):
    """Move ticket machines from traffic_sign tables to additional_sign tables."""

    help = "Move ticket machines from traffic_sign tables to additional_sign tables"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan_id_mapping: Dict[str, str] = {}
        self.migration_run: Optional[TicketMachineMigrationRun] = None
        self.stats = {
            "plans_processed": 0,
            "plans_migrated": 0,
            "plans_with_parent": 0,
            "plans_without_parent": 0,
            "plans_multiple_parents": 0,
            "plan_files_migrated": 0,
            "reals_processed": 0,
            "reals_migrated": 0,
            "reals_with_parent": 0,
            "reals_without_parent": 0,
            "reals_multiple_parents": 0,
            "real_files_migrated": 0,
            "device_types_updated": 0,
        }
        self.lost_data_records = []
        self.multiple_parent_warnings = []
        self.lost_field_values = {
            "value": set(),
            "txt": set(),
            "double_sided": set(),
            "peak_fastened": set(),
            "affect_area": set(),
        }

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making any changes",
        )
        parser.add_argument(
            "--hard-delete",
            action="store_true",
            help="Permanently delete original objects instead of soft-deleting them (default: soft-delete)",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        dry_run = options["dry_run"]
        hard_delete = options["hard_delete"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        if hard_delete:
            self.stdout.write(self.style.WARNING("HARD DELETE MODE - Original objects will be permanently deleted"))
        else:
            self.stdout.write("Soft-delete mode - Original objects will be marked as deleted but preserved in database")

        self.stdout.write("Starting ticket machine migration...")

        # Get system user for soft-delete operations
        system_user = get_system_user()

        # Create migration run record
        self.migration_run = TicketMachineMigrationRun.objects.create(
            executed_by=system_user,
            dry_run=dry_run,
            hard_delete=hard_delete,
        )
        self.stdout.write(f"Created migration run record: {self.migration_run.id}")

        try:
            # Wrap entire migration in a single atomic transaction
            with transaction.atomic():
                # Step 1: Update device type target_model FIRST (before creating objects)
                self._update_device_type_target_models(dry_run)

                # Step 2: Migrate TrafficSignPlan objects
                self._migrate_traffic_sign_plans(dry_run, hard_delete, system_user)

                # Step 3: Migrate TrafficSignReal objects
                self._migrate_traffic_sign_reals(dry_run, hard_delete, system_user)

                # For dry-run, rollback the entire transaction
                if dry_run:
                    transaction.set_rollback(True)

            # Update migration run record with success
            self.migration_run.completed_at = timezone.now()
            self.migration_run.success = True  # Mark as success (dry-run or real execution)
            self.migration_run.plans_processed = self.stats["plans_processed"]
            self.migration_run.plans_migrated = self.stats["plans_migrated"]
            self.migration_run.plans_with_parent = self.stats["plans_with_parent"]
            self.migration_run.plans_without_parent = self.stats["plans_without_parent"]
            self.migration_run.reals_processed = self.stats["reals_processed"]
            self.migration_run.reals_migrated = self.stats["reals_migrated"]
            self.migration_run.reals_with_parent = self.stats["reals_with_parent"]
            self.migration_run.reals_without_parent = self.stats["reals_without_parent"]
            self.migration_run.device_types_updated = self.stats["device_types_updated"]

            # Convert sets to sorted lists for JSON storage (include ALL fields, even empty ones)
            self.migration_run.lost_field_values = {
                field: sorted(list(values)) if values else [] for field, values in self.lost_field_values.items()
            }

            self.migration_run.save()

            # Step 4: Output report (outside transaction)
            self._output_report(dry_run)

            if dry_run:
                self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No changes were made"))
                self.stdout.write("Note: Migration run record and detail records were created for tracking")
            else:
                self.stdout.write(self.style.SUCCESS("\n✓ Migration completed successfully!"))

        except Exception as e:
            # Update migration run with error
            self.migration_run.completed_at = timezone.now()
            self.migration_run.success = False
            self.migration_run.error_message = str(e)
            self.migration_run.save()

            self.stdout.write(self.style.ERROR(f"\n✗ Migration failed: {str(e)}"))
            raise

    def _find_parent_sign_plan(self, ticket_machine: TrafficSignPlan) -> tuple[Optional[TrafficSignPlan], bool]:
        """Find parent sign (E2 or 521) on the same mount for a ticket machine plan.

        Returns:
            tuple: (parent_sign, multiple_parents_found)
        """
        if not ticket_machine.mount_plan:
            return None, False

        parent_candidates = TrafficSignPlan.objects.filter(
            mount_plan=ticket_machine.mount_plan,
            device_type__code__in=PARENT_SIGN_CODES,
            is_active=True,
        ).select_related("device_type")

        count = parent_candidates.count()

        if count == 0:
            return None, False
        elif count > 1:
            parent_ids = [str(p.id) for p in parent_candidates]
            warning = (
                f"TrafficSignPlan {ticket_machine.id} has multiple E2/521 signs on same mount_plan "
                f"({ticket_machine.mount_plan_id}). Parent candidates: {', '.join(parent_ids)}. "
                f"Assigning first: {parent_ids[0]}"
            )
            self.multiple_parent_warnings.append(warning)
            self.stats["plans_multiple_parents"] += 1
            return parent_candidates.first(), True

        return parent_candidates.first(), False

    def _find_parent_sign_real(self, ticket_machine: TrafficSignReal) -> tuple[Optional[TrafficSignReal], bool]:
        """Find parent sign (E2 or 521) on the same mount for a ticket machine real.

        Returns:
            tuple: (parent_sign, multiple_parents_found)
        """
        if not ticket_machine.mount_real:
            return None, False

        parent_candidates = TrafficSignReal.objects.filter(
            mount_real=ticket_machine.mount_real,
            device_type__code__in=PARENT_SIGN_CODES,
            is_active=True,
        ).select_related("device_type")

        count = parent_candidates.count()

        if count == 0:
            return None, False
        elif count > 1:
            parent_ids = [str(p.id) for p in parent_candidates]
            warning = (
                f"TrafficSignReal {ticket_machine.id} has multiple E2/521 signs on same mount_real "
                f"({ticket_machine.mount_real_id}). Parent candidates: {', '.join(parent_ids)}. "
                f"Assigning first: {parent_ids[0]}"
            )
            self.multiple_parent_warnings.append(warning)
            self.stats["reals_multiple_parents"] += 1
            return parent_candidates.first(), True

        return parent_candidates.first(), False

    def _record_lost_data(self, obj_type: str, obj_id: str, field_name: str, field_value: Any) -> None:
        """Record lost field data for audit trail and track unique values."""
        # Record all values including None - NULL is also lost data worth tracking
        self.lost_data_records.append(f"{obj_type},{obj_id},{field_name},{field_value}")

        # Track unique values for each field
        if field_name in self.lost_field_values:
            # Convert value to string for consistent storage
            value_str = str(field_value)
            if field_name == "affect_area":
                # For geometry fields, just track that it existed or was None
                value_str = "had_polygon" if field_value is not None else "None"
            elif field_name in ["double_sided", "peak_fastened"]:
                # For boolean fields, track True/False
                value_str = str(bool(field_value))

            self.lost_field_values[field_name].add(value_str)

    def _create_plan_detail_record(
        self,
        ts_plan: TrafficSignPlan,
        new_plan: Optional[AdditionalSignPlan],
        parent_sign: Optional[TrafficSignPlan],
        multiple_parents: bool,
        files_count: int,
    ) -> None:
        """Create detailed migration record for a TrafficSignPlan."""
        TicketMachineMigrationPlanRecord.objects.create(
            migration_run=self.migration_run,
            original_traffic_sign_plan=ts_plan,
            new_additional_sign_plan=new_plan,
            original_id=ts_plan.id,
            new_id=new_plan.id if new_plan else None,
            device_type_code=ts_plan.device_type.code,
            parent_found=parent_sign is not None,
            parent_sign_id=parent_sign.id if parent_sign else None,
            parent_sign_code=parent_sign.device_type.code if parent_sign else None,
            multiple_parents_found=multiple_parents,
            # Field tracking
            had_mount_plan=ts_plan.mount_plan is not None,
            had_plan=ts_plan.plan is not None,
            had_height=ts_plan.height is not None,
            had_size=ts_plan.size is not None,
            had_direction=ts_plan.direction is not None,
            had_reflection_class=ts_plan.reflection_class is not None,
            had_surface_class=ts_plan.surface_class is not None,
            had_mount_type=ts_plan.mount_type is not None,
            had_road_name=bool(ts_plan.road_name),
            had_lane_number=ts_plan.lane_number is not None,
            had_lane_type=ts_plan.lane_type is not None,
            had_location_specifier=ts_plan.location_specifier is not None,
            had_validity_period_start=ts_plan.validity_period_start is not None,
            had_validity_period_end=ts_plan.validity_period_end is not None,
            had_source_name=bool(ts_plan.source_name),
            had_source_id=bool(ts_plan.source_id),
            # Lost fields
            lost_value=str(ts_plan.value) if ts_plan.value is not None else "",
            lost_txt=ts_plan.txt if ts_plan.txt else "",
            lost_double_sided=ts_plan.double_sided,
            lost_peak_fastened=ts_plan.peak_fastened,
            had_affect_area=ts_plan.affect_area is not None,
            # Default values (all True for plans)
            set_color_to_blue=True,
            set_content_s_null=True,
            set_missing_content_false=True,
            set_additional_information_empty=True,
            files_migrated=files_count,
        )

    def _create_real_detail_record(
        self,
        ts_real: TrafficSignReal,
        new_real: Optional[AdditionalSignReal],
        parent_sign: Optional[TrafficSignReal],
        multiple_parents: bool,
        plan_mapping_found: bool,
        files_count: int,
    ) -> None:
        """Create detailed migration record for a TrafficSignReal."""
        TicketMachineMigrationRealRecord.objects.create(
            migration_run=self.migration_run,
            original_traffic_sign_real=ts_real,
            new_additional_sign_real=new_real,
            original_id=ts_real.id,
            new_id=new_real.id if new_real else None,
            device_type_code=ts_real.device_type.code,
            parent_found=parent_sign is not None,
            parent_sign_id=parent_sign.id if parent_sign else None,
            parent_sign_code=parent_sign.device_type.code if parent_sign else None,
            multiple_parents_found=multiple_parents,
            plan_mapping_found=plan_mapping_found,
            # Field tracking
            had_mount_real=ts_real.mount_real is not None,
            had_traffic_sign_plan=ts_real.traffic_sign_plan is not None,
            had_height=ts_real.height is not None,
            had_size=ts_real.size is not None,
            had_direction=ts_real.direction is not None,
            had_reflection_class=ts_real.reflection_class is not None,
            had_surface_class=ts_real.surface_class is not None,
            had_mount_type=ts_real.mount_type is not None,
            had_road_name=bool(ts_real.road_name),
            had_lane_number=ts_real.lane_number is not None,
            had_lane_type=ts_real.lane_type is not None,
            had_location_specifier=ts_real.location_specifier is not None,
            had_legacy_code=bool(ts_real.legacy_code),
            had_installation_id=bool(ts_real.installation_id),
            had_installation_details=bool(ts_real.installation_details),
            had_permit_decision_id=bool(ts_real.permit_decision_id),
            had_scanned_at=ts_real.scanned_at is not None,
            had_manufacturer=bool(ts_real.manufacturer),
            had_rfid=bool(ts_real.rfid),
            had_operation=bool(ts_real.operation),
            had_attachment_url=bool(ts_real.attachment_url),
            had_validity_period_start=ts_real.validity_period_start is not None,
            had_validity_period_end=ts_real.validity_period_end is not None,
            had_source_name=bool(ts_real.source_name),
            had_source_id=bool(ts_real.source_id),
            had_installation_status=ts_real.installation_status is not None,
            had_installation_date=ts_real.installation_date is not None,
            had_installation_status_note=False,  # Field doesn't exist in TrafficSignReal
            # Lost fields
            lost_value=str(ts_real.value) if ts_real.value is not None else "",
            lost_txt=ts_real.txt if ts_real.txt else "",
            lost_double_sided=ts_real.double_sided,
            lost_peak_fastened=ts_real.peak_fastened,
            # Default values (all True for reals)
            set_color_to_blue=True,
            set_content_s_null=True,
            set_missing_content_false=True,
            set_additional_information_empty=True,
            set_installed_by_null=True,
            files_migrated=files_count,
        )

    def _migrate_traffic_sign_plans(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignPlan ticket machines to AdditionalSignPlan."""
        self.stdout.write("\n=== Migrating TrafficSignPlan objects ===")

        traffic_sign_plans = TrafficSignPlan.objects.filter(
            device_type__code__in=TICKET_MACHINE_CODES,
            is_active=True,
        ).select_related("device_type", "mount_plan", "plan", "owner", "created_by", "updated_by")

        self.stats["plans_processed"] = traffic_sign_plans.count()
        self.stdout.write(f"Found {self.stats['plans_processed']} TrafficSignPlan ticket machines")

        for ts_plan in traffic_sign_plans:
            self.stdout.write(f"  Processing TrafficSignPlan {ts_plan.id}...")

            # Find parent sign
            parent_sign, multiple_parents = self._find_parent_sign_plan(ts_plan)
            if parent_sign:
                self.stats["plans_with_parent"] += 1
                self.stdout.write(f"    → Found parent sign: {parent_sign.id} ({parent_sign.device_type.code})")
            else:
                self.stats["plans_without_parent"] += 1
                self.stdout.write("    → No parent sign found")

            # Record lost data
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "value", ts_plan.value)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "txt", ts_plan.txt)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "double_sided", ts_plan.double_sided)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "peak_fastened", ts_plan.peak_fastened)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "affect_area", ts_plan.affect_area)

            new_plan = None
            file_count = 0

            if not dry_run:
                # Prepare unique source values by concatenating with migration identifier
                # This preserves original source tracking while avoiding unique constraint violations
                migration_suffix = f"_migrated_run_{self.migration_run.id}"
                # Concatenate original values with migration identifier (use 'unknown' if empty)
                new_source_name = f"{ts_plan.source_name or 'unknown'}{migration_suffix}"

                # Create AdditionalSignPlan
                new_plan = AdditionalSignPlan.objects.create(
                    parent=parent_sign,
                    mount_plan=ts_plan.mount_plan,
                    plan=ts_plan.plan,
                    device_type=ts_plan.device_type,
                    location=ts_plan.location,
                    height=ts_plan.height,
                    size=ts_plan.size,
                    direction=ts_plan.direction,
                    reflection_class=ts_plan.reflection_class,
                    surface_class=ts_plan.surface_class,
                    color=Color.BLUE,
                    mount_type=ts_plan.mount_type,
                    road_name=ts_plan.road_name,
                    lane_number=ts_plan.lane_number,
                    lane_type=ts_plan.lane_type,
                    location_specifier=ts_plan.location_specifier,
                    content_s=None,
                    missing_content=False,
                    additional_information="",
                    owner=ts_plan.owner,
                    validity_period_start=ts_plan.validity_period_start,
                    validity_period_end=ts_plan.validity_period_end,
                    source_name=new_source_name,
                    source_id=ts_plan.source_id,  # Keep original ID for traceability, but ensure source_name is unique
                    created_at=ts_plan.created_at,
                    updated_at=ts_plan.updated_at,
                    created_by=ts_plan.created_by,
                    updated_by=ts_plan.updated_by,
                )

                # Store mapping for later use in Real migration
                self.plan_id_mapping[str(ts_plan.id)] = str(new_plan.id)

                # Migrate files
                files = TrafficSignPlanFile.objects.filter(traffic_sign_plan=ts_plan)
                file_count = files.count()
                for file_obj in files:
                    AdditionalSignPlanFile.objects.create(
                        file=file_obj.file,
                        additional_sign_plan=new_plan,
                    )
                self.stats["plan_files_migrated"] += file_count

                # Delete original based on mode
                if hard_delete:
                    ts_plan.delete()
                else:
                    ts_plan.soft_delete(system_user)

                self.stats["plans_migrated"] += 1
                self.stdout.write(f"    ✓ Created AdditionalSignPlan {new_plan.id}")

            # Create detail record (outside dry_run check so we log even in dry-run)
            self._create_plan_detail_record(ts_plan, new_plan, parent_sign, multiple_parents, file_count)

    def _migrate_traffic_sign_reals(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignReal ticket machines to AdditionalSignReal."""
        self.stdout.write("\n=== Migrating TrafficSignReal objects ===")

        traffic_sign_reals = TrafficSignReal.objects.filter(
            device_type__code__in=TICKET_MACHINE_CODES,
            is_active=True,
        ).select_related(
            "device_type",
            "mount_real",
            "traffic_sign_plan",
            "owner",
            "created_by",
            "updated_by",
        )

        self.stats["reals_processed"] = traffic_sign_reals.count()
        self.stdout.write(f"Found {self.stats['reals_processed']} TrafficSignReal ticket machines")

        for ts_real in traffic_sign_reals:
            self._process_single_traffic_sign_real(ts_real, dry_run, hard_delete, system_user)

    def _process_single_traffic_sign_real(
        self, ts_real: TrafficSignReal, dry_run: bool, hard_delete: bool, system_user: Any
    ) -> None:
        """Process a single TrafficSignReal migration."""
        self.stdout.write(f"  Processing TrafficSignReal {ts_real.id}...")

        # Find parent sign
        parent_sign, multiple_parents = self._find_parent_sign_real(ts_real)
        self._log_parent_status(parent_sign, is_plan=False)

        # Map traffic_sign_plan to additional_sign_plan
        additional_sign_plan_id, plan_mapping_found = self._get_plan_mapping(ts_real, dry_run)

        # Record lost data
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "value", ts_real.value)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "txt", ts_real.txt)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "double_sided", ts_real.double_sided)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "peak_fastened", ts_real.peak_fastened)

        new_real = None
        file_count = 0

        if not dry_run:
            new_real, file_count = self._create_additional_sign_real(
                ts_real, parent_sign, additional_sign_plan_id, hard_delete, system_user
            )

        # Create detail record (outside dry_run check so we log even in dry-run)
        self._create_real_detail_record(
            ts_real, new_real, parent_sign, multiple_parents, plan_mapping_found, file_count
        )

    def _log_parent_status(self, parent_sign: Any, is_plan: bool) -> None:
        """Log parent sign status."""
        if parent_sign:
            stat_key = "plans_with_parent" if is_plan else "reals_with_parent"
            self.stats[stat_key] += 1
            self.stdout.write(f"    → Found parent sign: {parent_sign.id} ({parent_sign.device_type.code})")
        else:
            stat_key = "plans_without_parent" if is_plan else "reals_without_parent"
            self.stats[stat_key] += 1
            self.stdout.write("    → No parent sign found")

    def _get_plan_mapping(self, ts_real: TrafficSignReal, dry_run: bool) -> tuple[Any, bool]:
        """Get plan mapping for a TrafficSignReal."""
        additional_sign_plan_id = None
        plan_mapping_found = False

        if ts_real.traffic_sign_plan_id:
            additional_sign_plan_id = self.plan_id_mapping.get(str(ts_real.traffic_sign_plan_id))
            plan_mapping_found = additional_sign_plan_id is not None
            if additional_sign_plan_id and not dry_run:
                self.stdout.write(f"    → Mapped plan: {ts_real.traffic_sign_plan_id} → {additional_sign_plan_id}")

        return additional_sign_plan_id, plan_mapping_found

    def _create_additional_sign_real(
        self,
        ts_real: TrafficSignReal,
        parent_sign: Any,
        additional_sign_plan_id: Any,
        hard_delete: bool,
        system_user: Any,
    ) -> tuple[AdditionalSignReal, int]:
        """Create AdditionalSignReal and migrate files."""
        # Get the AdditionalSignPlan object if we have an ID
        additional_sign_plan_obj = None
        if additional_sign_plan_id:
            additional_sign_plan_obj = AdditionalSignPlan.objects.get(id=additional_sign_plan_id)

        # Prepare unique source values
        migration_suffix = f"_migrated_run_{self.migration_run.id}"
        new_source_name = f"{ts_real.source_name or 'unknown'}{migration_suffix}"

        # Create AdditionalSignReal
        new_real = AdditionalSignReal.objects.create(
            parent=parent_sign,
            additional_sign_plan=additional_sign_plan_obj,
            mount_real=ts_real.mount_real,
            device_type=ts_real.device_type,
            location=ts_real.location,
            height=ts_real.height,
            size=ts_real.size,
            direction=ts_real.direction,
            reflection_class=ts_real.reflection_class,
            surface_class=ts_real.surface_class,
            color=Color.BLUE,
            mount_type=ts_real.mount_type,
            road_name=ts_real.road_name,
            lane_number=ts_real.lane_number,
            lane_type=ts_real.lane_type,
            location_specifier=ts_real.location_specifier,
            legacy_code=ts_real.legacy_code,
            installation_id=ts_real.installation_id,
            installation_details=ts_real.installation_details,
            permit_decision_id=ts_real.permit_decision_id,
            scanned_at=ts_real.scanned_at,
            manufacturer=ts_real.manufacturer,
            rfid=ts_real.rfid,
            operation=ts_real.operation,
            attachment_url=ts_real.attachment_url,
            content_s=None,
            missing_content=False,
            additional_information="",
            installed_by=None,
            owner=ts_real.owner,
            validity_period_start=ts_real.validity_period_start,
            validity_period_end=ts_real.validity_period_end,
            source_name=new_source_name,
            source_id=ts_real.source_id,
            installation_status=ts_real.installation_status,
            installation_date=ts_real.installation_date,
            created_at=ts_real.created_at,
            updated_at=ts_real.updated_at,
            created_by=ts_real.created_by,
            updated_by=ts_real.updated_by,
        )

        # Migrate files
        file_count = self._migrate_real_files(ts_real, new_real)

        # Delete original based on mode
        self._delete_original_traffic_sign_real(ts_real, hard_delete, system_user)

        self.stats["reals_migrated"] += 1
        self.stdout.write(f"    ✓ Created AdditionalSignReal {new_real.id}")

        return new_real, file_count

    def _migrate_real_files(self, ts_real: TrafficSignReal, new_real: AdditionalSignReal) -> int:
        """Migrate files from TrafficSignReal to AdditionalSignReal."""
        files = TrafficSignRealFile.objects.filter(traffic_sign_real=ts_real)
        file_count = files.count()
        for file_obj in files:
            AdditionalSignRealFile.objects.create(
                file=file_obj.file,
                additional_sign_real=new_real,
            )
        self.stats["real_files_migrated"] += file_count
        return file_count

    def _delete_original_traffic_sign_real(self, ts_real: TrafficSignReal, hard_delete: bool, system_user: Any) -> None:
        """Delete or soft-delete the original TrafficSignReal."""
        if hard_delete:
            ts_real.delete()
        else:
            ts_real.soft_delete(system_user)

    def _update_device_type_target_models(self, dry_run: bool) -> None:
        """Update device type target_model for ticket machine codes."""
        self.stdout.write("\n=== Updating device type target_model ===")

        device_types = TrafficControlDeviceType.objects.filter(code__in=TICKET_MACHINE_CODES)
        self.stats["device_types_updated"] = device_types.count()

        self.stdout.write(f"Found {self.stats['device_types_updated']} device types to update")

        if not dry_run:
            updated = device_types.update(target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)
            self.stdout.write(f"  ✓ Updated {updated} device type(s)")
        else:
            for dt in device_types:
                self.stdout.write(f"  Would update: {dt.code} → ADDITIONAL_SIGN")

    def _output_report(self, dry_run: bool) -> None:
        """Output comprehensive migration report."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("MIGRATION REPORT"))
        self.stdout.write("=" * 80)

        # Plans summary
        self.stdout.write("\n📋 TrafficSignPlan Migration:")
        self.stdout.write(f"  • Processed: {self.stats['plans_processed']}")
        self.stdout.write(f"  • Migrated: {self.stats['plans_migrated']}")
        self.stdout.write(f"  • With parent (E2/521): {self.stats['plans_with_parent']}")
        self.stdout.write(f"  • Without parent: {self.stats['plans_without_parent']}")
        self.stdout.write(f"  • Multiple parents found: {self.stats['plans_multiple_parents']}")
        self.stdout.write(f"  • Files migrated: {self.stats['plan_files_migrated']}")

        # Reals summary
        self.stdout.write("\n📍 TrafficSignReal Migration:")
        self.stdout.write(f"  • Processed: {self.stats['reals_processed']}")
        self.stdout.write(f"  • Migrated: {self.stats['reals_migrated']}")
        self.stdout.write(f"  • With parent (E2/521): {self.stats['reals_with_parent']}")
        self.stdout.write(f"  • Without parent: {self.stats['reals_without_parent']}")
        self.stdout.write(f"  • Multiple parents found: {self.stats['reals_multiple_parents']}")
        self.stdout.write(f"  • Files migrated: {self.stats['real_files_migrated']}")

        # Device types
        self.stdout.write("\n🔧 Device Types:")
        self.stdout.write(f"  • Target model updated: {self.stats['device_types_updated']}")

        # Multiple parent warnings
        if self.multiple_parent_warnings:
            self.stdout.write("\n⚠️  Multiple Parent Warnings:")
            for warning in self.multiple_parent_warnings:
                self.stdout.write(f"  • {warning}")

        # Lost data summary
        if self.lost_data_records and not dry_run:
            self.stdout.write(f"\n📝 Lost field data recorded: {len(self.lost_data_records)} entries")
            self._save_lost_data_report()

        self.stdout.write("\n" + "=" * 80)

    def _save_lost_data_report(self) -> None:
        """Save lost field data to a CSV file in agent_docs."""
        import os
        from datetime import datetime

        agent_docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "agent_docs",
        )
        os.makedirs(agent_docs_dir, exist_ok=True)

        filename = f"ticket_machine_migration_lost_fields_{datetime.now().strftime('%Y-%m-%d')}.csv"
        filepath = os.path.join(agent_docs_dir, filename)

        with open(filepath, "w") as f:
            f.write("object_type,object_id,field_name,field_value\n")
            for record in self.lost_data_records:
                f.write(f"{record}\n")

        self.stdout.write(f"  → Saved to: {filepath}")
