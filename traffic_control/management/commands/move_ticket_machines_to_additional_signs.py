"""
Management command to move ticket machines from traffic_sign tables to additional_sign tables.

This command migrates ticket machine objects (device type codes H20.91, H20.92, H20.93, 8591, 8592, 8593)
from TrafficSignReal/TrafficSignPlan to AdditionalSignReal/AdditionalSignPlan.
"""
import logging
from datetime import datetime
from typing import Any, Optional

from django.utils import timezone

from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.management.commands.base_migration import BaseMigrationCommand
from traffic_control.models.additional_sign import (
    AdditionalSignPlan,
    AdditionalSignPlanFile,
    AdditionalSignReal,
    AdditionalSignRealFile,
    Color,
)
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

logger = logging.getLogger(__name__)

PARENT_SIGN_CODES = ["E2", "521"]


class Command(BaseMigrationCommand):
    """Move ticket machines from traffic_sign tables to additional_sign tables."""

    help = "Move ticket machines from traffic_sign tables to additional_sign tables"

    def __init__(self, *args, **kwargs):
        """Initialize ticket machine migration command."""
        super().__init__(*args, **kwargs)
        self.multiple_parent_warnings = []
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
        self.lost_field_values = {
            "value": set(),
            "txt": set(),
            "double_sided": set(),
            "peak_fastened": set(),
            "affect_area": set(),
        }

    # Implement abstract methods from base class

    def get_migration_start_message(self) -> str:
        """Get the migration start message."""
        return "Starting ticket machine migration..."

    def create_migration_run(self, system_user: Any, dry_run: bool, hard_delete: bool) -> TicketMachineMigrationRun:
        """Create migration run record."""
        return TicketMachineMigrationRun.objects.create(
            executed_by=system_user,
            dry_run=dry_run,
            hard_delete=hard_delete,
        )

    def update_migration_run_success(self, dry_run: bool) -> None:
        """Update migration run with success status and statistics."""
        self.migration_run.completed_at = timezone.now()
        self.migration_run.success = True
        self.migration_run.plans_processed = self.stats["plans_processed"]
        self.migration_run.plans_migrated = self.stats["plans_migrated"]
        self.migration_run.plans_with_parent = self.stats["plans_with_parent"]
        self.migration_run.plans_without_parent = self.stats["plans_without_parent"]
        self.migration_run.reals_processed = self.stats["reals_processed"]
        self.migration_run.reals_migrated = self.stats["reals_migrated"]
        self.migration_run.reals_with_parent = self.stats["reals_with_parent"]
        self.migration_run.reals_without_parent = self.stats["reals_without_parent"]
        self.migration_run.device_types_updated = self.stats["device_types_updated"]

        # Convert sets to sorted lists for JSON storage
        self.migration_run.lost_field_values = {
            field: sorted(values) if values else [] for field, values in self.lost_field_values.items()
        }

        self.migration_run.save()

    def get_device_codes(self) -> list:
        """Get device codes to migrate."""
        return TICKET_MACHINE_CODES

    def get_target_device_type_model(self) -> DeviceTypeTargetModel:
        """Get target device type model enum."""
        return DeviceTypeTargetModel.ADDITIONAL_SIGN

    def output_migration_specific_report(self) -> None:
        """Output migration-specific parts of the report."""
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

    def output_additional_warnings(self) -> None:
        """Output any additional warnings specific to the migration."""
        if self.multiple_parent_warnings:
            self.stdout.write("\n⚠️  Multiple Parent Warnings:")
            for warning in self.multiple_parent_warnings:
                self.stdout.write(f"  • {warning}")

    def get_lost_data_report_filename(self) -> str:
        """Get filename for lost data report."""
        return f"ticket_machine_migration_lost_fields_{datetime.now().strftime('%Y-%m-%d')}.csv"

    # Migration-specific methods

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
            # Field tracking
            **self._get_plan_field_tracking_kwargs(ts_plan),
            migration_run=self.migration_run,
            original_traffic_sign_plan=ts_plan,
            new_additional_sign_plan=new_plan,
            original_id=ts_plan.id,
            new_id=new_plan.id if new_plan else None,
            device_type_code=ts_plan.device_type.code,
            parent_found=parent_sign is not None,
            parent_sign_id=parent_sign.id if parent_sign else None,
            parent_sign_code=parent_sign.device_type.code if parent_sign else "",
            multiple_parents_found=multiple_parents,
            had_mount_plan=ts_plan.mount_plan is not None,
            had_plan=ts_plan.plan is not None,
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
            # Field tracking
            **self._get_real_field_tracking_kwargs(ts_real),
            migration_run=self.migration_run,
            original_traffic_sign_real=ts_real,
            new_additional_sign_real=new_real,
            original_id=ts_real.id,
            new_id=new_real.id if new_real else None,
            device_type_code=ts_real.device_type.code,
            parent_found=parent_sign is not None,
            parent_sign_id=parent_sign.id if parent_sign else None,
            parent_sign_code=parent_sign.device_type.code if parent_sign else "",
            multiple_parents_found=multiple_parents,
            plan_mapping_found=plan_mapping_found,
            had_mount_real=ts_real.mount_real is not None,
            had_traffic_sign_plan=ts_real.traffic_sign_plan is not None,
            had_legacy_code=bool(ts_real.legacy_code),
            had_installation_id=bool(ts_real.installation_id),
            had_installation_details=bool(ts_real.installation_details),
            had_permit_decision_id=bool(ts_real.permit_decision_id),
            had_scanned_at=ts_real.scanned_at is not None,
            had_manufacturer=bool(ts_real.manufacturer),
            had_rfid=bool(ts_real.rfid),
            had_operation=bool(ts_real.operation),
            had_attachment_url=bool(ts_real.attachment_url),
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
                new_source_name = self._generate_unique_source_name(ts_plan.source_name)

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
                file_count = self._migrate_files(files, AdditionalSignPlanFile, "additional_sign_plan", new_plan)
                self.stats["plan_files_migrated"] += file_count

                self.stats["plans_migrated"] += 1
                self.stdout.write(f"    ✓ Created AdditionalSignPlan {new_plan.id}")

            # Create detail record (outside dry_run check so we log even in dry-run)
            self._create_plan_detail_record(ts_plan, new_plan, parent_sign, multiple_parents, file_count)

            if not dry_run:
                self._delete_original_traffic_sign_real(ts_plan, hard_delete, system_user)

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
        if parent_sign:
            self.stats["reals_with_parent"] += 1
            self.stdout.write(f"    → Found parent sign: {parent_sign.id} ({parent_sign.device_type.code})")
        else:
            self.stats["reals_without_parent"] += 1
            self.stdout.write("    → No parent sign found")

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
            new_real, file_count = self._create_additional_sign_real(ts_real, parent_sign, additional_sign_plan_id)

        # Create detail record (outside dry_run check so we log even in dry-run)
        self._create_real_detail_record(
            ts_real, new_real, parent_sign, multiple_parents, plan_mapping_found, file_count
        )

        if not dry_run:
            self._delete_original_traffic_sign_real(ts_real, hard_delete, system_user)

    def _create_additional_sign_real(
        self,
        ts_real: TrafficSignReal,
        parent_sign: Any,
        additional_sign_plan_id: Any,
    ) -> tuple[AdditionalSignReal, int]:
        """Create AdditionalSignReal and migrate files."""
        # Get the AdditionalSignPlan object if we have an ID
        additional_sign_plan_obj = None
        if additional_sign_plan_id:
            additional_sign_plan_obj = AdditionalSignPlan.objects.get(id=additional_sign_plan_id)

        # Prepare unique source values
        new_source_name = self._generate_unique_source_name(ts_real.source_name)

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
        files = TrafficSignRealFile.objects.filter(traffic_sign_real=ts_real)
        file_count = self._migrate_files(files, AdditionalSignRealFile, "additional_sign_real", new_real)
        self.stats["real_files_migrated"] += file_count

        self.stats["reals_migrated"] += 1
        self.stdout.write(f"    ✓ Created AdditionalSignReal {new_real.id}")

        return new_real, file_count
