"""
Management command to move traffic signs from traffic_sign tables to signpost tables.
This command migrates traffic sign objects with specific device type codes
(6211-62324, 6511-6524, F24.x, F7.2, F8.1) from TrafficSignPlan/TrafficSignReal
to SignpostPlan/SignpostReal tables.
"""
import logging
from datetime import datetime
from typing import Any, Optional

from django.utils import timezone

from traffic_control.constants import SIGNPOST_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.management.commands.base_migration import BaseMigrationCommand
from traffic_control.models.signpost import SignpostPlan, SignpostPlanFile, SignpostReal, SignpostRealFile
from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)
from traffic_control.models.traffic_sign import (
    TrafficSignPlan,
    TrafficSignPlanFile,
    TrafficSignReal,
    TrafficSignRealFile,
)

logger = logging.getLogger(__name__)


class Command(BaseMigrationCommand):
    """Move traffic signs from traffic_sign tables to signpost tables."""

    help = "Move traffic signs with specific device codes from traffic_sign tables to signpost tables"

    def __init__(self, *args, **kwargs):
        """Initialize signpost migration command."""
        super().__init__(*args, **kwargs)
        self.stats = {
            "plans_processed": 0,
            "plans_migrated": 0,
            "plan_files_migrated": 0,
            "reals_processed": 0,
            "reals_migrated": 0,
            "real_files_migrated": 0,
            "device_types_updated": 0,
        }
        self.lost_field_values = {
            "surface_class": set(),
            "peak_fastened": set(),
            "affect_area": set(),
            "installation_id": set(),
            "installation_details": set(),
            "permit_decision_id": set(),
            "rfid": set(),
            "operation": set(),
        }

    # Implement abstract methods from base class

    def get_migration_start_message(self) -> str:
        """Get the migration start message."""
        return "Starting traffic sign to signpost migration..."

    def create_migration_run(self, system_user: Any, dry_run: bool, hard_delete: bool) -> SignpostMigrationRun:
        """Create migration run record."""
        return SignpostMigrationRun.objects.create(
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
        self.migration_run.reals_processed = self.stats["reals_processed"]
        self.migration_run.reals_migrated = self.stats["reals_migrated"]
        self.migration_run.plan_files_migrated = self.stats["plan_files_migrated"]
        self.migration_run.real_files_migrated = self.stats["real_files_migrated"]
        self.migration_run.device_types_updated = self.stats["device_types_updated"]

        # Convert sets to sorted lists for JSON storage
        self.migration_run.lost_field_values = {
            field: sorted(values) if values else [] for field, values in self.lost_field_values.items()
        }

        self.migration_run.save()

    def get_device_codes(self) -> list:
        """Get device codes to migrate."""
        return SIGNPOST_CODES

    def get_target_device_type_model(self) -> DeviceTypeTargetModel:
        """Get target device type model enum."""
        return DeviceTypeTargetModel.SIGNPOST

    def output_migration_specific_report(self) -> None:
        """Output migration-specific parts of the report."""
        self.stdout.write("\n📋 TrafficSignPlan Migration:")
        self.stdout.write(f"  • Processed: {self.stats['plans_processed']}")
        self.stdout.write(f"  • Migrated: {self.stats['plans_migrated']}")
        self.stdout.write(f"  • Files migrated: {self.stats['plan_files_migrated']}")

        self.stdout.write("\n📍 TrafficSignReal Migration:")
        self.stdout.write(f"  • Processed: {self.stats['reals_processed']}")
        self.stdout.write(f"  • Migrated: {self.stats['reals_migrated']}")
        self.stdout.write(f"  • Files migrated: {self.stats['real_files_migrated']}")

    def output_additional_warnings(self) -> None:
        """Output any additional warnings specific to the migration."""
        pass  # No additional warnings for signpost migration

    def get_lost_data_report_filename(self) -> str:
        """Get filename for lost data report."""
        return f"signpost_migration_lost_fields_{datetime.now().strftime('%Y-%m-%d')}.csv"

    # Migration-specific methods
    def _create_plan_detail_record(
        self,
        ts_plan: TrafficSignPlan,
        new_plan: Optional[SignpostPlan],
        files_count: int,
    ) -> None:
        """Create detailed migration record for a TrafficSignPlan."""
        SignpostMigrationPlanRecord.objects.create(
            **self._get_plan_field_tracking_kwargs(ts_plan),
            migration_run=self.migration_run,
            original_traffic_sign_plan=ts_plan,
            new_signpost_plan=new_plan,
            original_id=ts_plan.id,
            new_id=new_plan.id if new_plan else None,
            device_type_code=ts_plan.device_type.code,
            had_mount_plan=ts_plan.mount_plan is not None,
            had_plan=ts_plan.plan is not None,
            lost_surface_class=str(ts_plan.surface_class) if ts_plan.surface_class else "",
            lost_peak_fastened=ts_plan.peak_fastened,
            had_affect_area=ts_plan.affect_area is not None,
            files_migrated=files_count,
        )

    def _create_real_detail_record(
        self,
        ts_real: TrafficSignReal,
        new_real: Optional[SignpostReal],
        plan_mapping_found: bool,
        files_count: int,
    ) -> None:
        """Create detailed migration record for a TrafficSignReal."""
        SignpostMigrationRealRecord.objects.create(
            **self._get_real_field_tracking_kwargs(ts_real),
            migration_run=self.migration_run,
            original_traffic_sign_real=ts_real,
            new_signpost_real=new_real,
            original_id=ts_real.id,
            new_id=new_real.id if new_real else None,
            device_type_code=ts_real.device_type.code,
            plan_mapping_found=plan_mapping_found,
            had_mount_real=ts_real.mount_real is not None,
            had_traffic_sign_plan=ts_real.traffic_sign_plan is not None,
            had_legacy_code=bool(ts_real.legacy_code),
            had_scanned_at=ts_real.scanned_at is not None,
            had_manufacturer=bool(ts_real.manufacturer),
            had_installation_status=ts_real.installation_status is not None,
            had_installation_date=ts_real.installation_date is not None,
            had_condition=ts_real.condition is not None,
            lost_surface_class=str(ts_real.surface_class) if ts_real.surface_class else "",
            lost_peak_fastened=ts_real.peak_fastened,
            lost_installation_id=ts_real.installation_id if ts_real.installation_id else "",
            lost_installation_details=ts_real.installation_details if ts_real.installation_details else "",
            lost_permit_decision_id=ts_real.permit_decision_id if ts_real.permit_decision_id else "",
            lost_rfid=ts_real.rfid if ts_real.rfid else "",
            lost_operation=ts_real.operation if ts_real.operation else "",
            lost_attachment_url="",
            files_migrated=files_count,
        )

    def _migrate_traffic_sign_plans(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignPlan objects to SignpostPlan."""
        self.stdout.write("\n=== Migrating TrafficSignPlan objects ===")
        traffic_sign_plans = TrafficSignPlan.objects.filter(
            device_type__code__in=SIGNPOST_CODES,
            is_active=True,
        ).select_related("device_type", "mount_plan", "plan", "owner", "created_by", "updated_by")
        self.stats["plans_processed"] = traffic_sign_plans.count()
        self.stdout.write(f"Found {self.stats['plans_processed']} TrafficSignPlan objects with signpost codes")
        for ts_plan in traffic_sign_plans:
            self.stdout.write(f"  Processing TrafficSignPlan {ts_plan.id} ({ts_plan.device_type.code})...")
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "surface_class", ts_plan.surface_class)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "peak_fastened", ts_plan.peak_fastened)
            self._record_lost_data("TrafficSignPlan", str(ts_plan.id), "affect_area", ts_plan.affect_area)
            new_plan = None
            file_count = 0
            if not dry_run:
                new_source_name = self._generate_unique_source_name(ts_plan.source_name)
                new_plan = SignpostPlan.objects.create(
                    parent=None,
                    mount_plan=ts_plan.mount_plan,
                    plan=ts_plan.plan,
                    device_type=ts_plan.device_type,
                    location=ts_plan.location,
                    height=ts_plan.height,
                    size=ts_plan.size,
                    direction=ts_plan.direction,
                    reflection_class=ts_plan.reflection_class,
                    value=ts_plan.value,
                    txt=ts_plan.txt,
                    mount_type=ts_plan.mount_type,
                    road_name=ts_plan.road_name,
                    lane_number=ts_plan.lane_number,
                    lane_type=ts_plan.lane_type,
                    location_specifier=ts_plan.location_specifier,
                    double_sided=ts_plan.double_sided,
                    attachment_class=None,
                    target_id=None,
                    target_txt=None,
                    electric_maintainer=None,
                    owner=ts_plan.owner,
                    validity_period_start=ts_plan.validity_period_start,
                    validity_period_end=ts_plan.validity_period_end,
                    source_name=new_source_name,
                    source_id=ts_plan.source_id,
                    created_at=ts_plan.created_at,
                    updated_at=ts_plan.updated_at,
                    created_by=ts_plan.created_by,
                    updated_by=ts_plan.updated_by,
                )
                self.plan_id_mapping[str(ts_plan.id)] = str(new_plan.id)
                files = TrafficSignPlanFile.objects.filter(traffic_sign_plan=ts_plan)
                file_count = self._migrate_files(files, SignpostPlanFile, "signpost_plan", new_plan)
                self.stats["plan_files_migrated"] += file_count
                self.stats["plans_migrated"] += 1
                self.stdout.write(f"    ✓ Created SignpostPlan {new_plan.id}")

            # Create detail record (outside dry_run check so we log even in dry-run)
            self._create_plan_detail_record(ts_plan, new_plan, file_count)

            if not dry_run:
                self._delete_original_traffic_sign_real(ts_plan, hard_delete, system_user)

    def _migrate_traffic_sign_reals(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignReal objects to SignpostReal."""
        self.stdout.write("\n=== Migrating TrafficSignReal objects ===")
        traffic_sign_reals = TrafficSignReal.objects.filter(
            device_type__code__in=SIGNPOST_CODES,
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
        self.stdout.write(f"Found {self.stats['reals_processed']} TrafficSignReal objects with signpost codes")
        for ts_real in traffic_sign_reals:
            self._process_single_traffic_sign_real(ts_real, dry_run, hard_delete, system_user)

    def _process_single_traffic_sign_real(
        self, ts_real: TrafficSignReal, dry_run: bool, hard_delete: bool, system_user: Any
    ) -> None:
        """Process a single TrafficSignReal migration."""
        self.stdout.write(f"  Processing TrafficSignReal {ts_real.id} ({ts_real.device_type.code})...")
        signpost_plan_id, plan_mapping_found = self._get_plan_mapping(ts_real, dry_run)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "surface_class", ts_real.surface_class)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "peak_fastened", ts_real.peak_fastened)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "installation_id", ts_real.installation_id)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "installation_details", ts_real.installation_details)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "permit_decision_id", ts_real.permit_decision_id)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "rfid", ts_real.rfid)
        self._record_lost_data("TrafficSignReal", str(ts_real.id), "operation", ts_real.operation)

        new_real = None
        file_count = 0
        if not dry_run:
            new_real, file_count = self._create_signpost_real(ts_real, signpost_plan_id)
            self.stats["reals_migrated"] += 1

        # Create detail record (outside dry_run check so we log even in dry-run)
        self._create_real_detail_record(ts_real, new_real, plan_mapping_found, file_count)

        if not dry_run:
            self._delete_original_traffic_sign_real(ts_real, hard_delete, system_user)

    def _create_signpost_real(
        self,
        ts_real: TrafficSignReal,
        signpost_plan_id: Any,
    ) -> tuple[SignpostReal, int]:
        """Create SignpostReal and migrate files."""
        signpost_plan_obj = None
        if signpost_plan_id:
            signpost_plan_obj = SignpostPlan.objects.get(id=signpost_plan_id)

        new_source_name = self._generate_unique_source_name(ts_real.source_name)
        new_real = SignpostReal.objects.create(
            parent=None,
            signpost_plan=signpost_plan_obj,
            mount_real=ts_real.mount_real,
            device_type=ts_real.device_type,
            location=ts_real.location,
            height=ts_real.height,
            size=ts_real.size,
            direction=ts_real.direction,
            reflection_class=ts_real.reflection_class,
            value=ts_real.value,
            txt=ts_real.txt,
            mount_type=ts_real.mount_type,
            road_name=ts_real.road_name,
            lane_number=ts_real.lane_number,
            lane_type=ts_real.lane_type,
            location_specifier=ts_real.location_specifier,
            double_sided=ts_real.double_sided,
            scanned_at=ts_real.scanned_at,
            manufacturer=ts_real.manufacturer,
            material=None,
            organization=None,
            attachment_class=None,
            attachment_url=ts_real.attachment_url,
            target_id=None,
            target_txt=None,
            electric_maintainer=None,
            owner=ts_real.owner,
            validity_period_start=ts_real.validity_period_start,
            validity_period_end=ts_real.validity_period_end,
            source_name=new_source_name,
            source_id=ts_real.source_id,
            installation_status=ts_real.installation_status,
            installation_date=ts_real.installation_date,
            condition=ts_real.condition,
            created_at=ts_real.created_at,
            updated_at=ts_real.updated_at,
            created_by=ts_real.created_by,
            updated_by=ts_real.updated_by,
        )
        files = TrafficSignRealFile.objects.filter(traffic_sign_real=ts_real)
        file_count = self._migrate_files(files, SignpostRealFile, "signpost_real", new_real)
        self.stats["real_files_migrated"] += file_count
        self.stdout.write(f"    ✓ Created SignpostReal {new_real.id}")
        return new_real, file_count
