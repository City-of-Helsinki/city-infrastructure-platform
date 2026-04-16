"""Base class for traffic sign migration commands with shared functionality."""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from auditlog.context import set_actor
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.models.traffic_sign import TrafficSignPlan, TrafficSignReal
from users.utils import get_system_user

logger = logging.getLogger(__name__)


class BaseMigrationCommand(BaseCommand, ABC):
    """Base class for migration commands with shared functionality."""

    def __init__(self, *args, **kwargs):
        """Initialize base migration command."""
        super().__init__(*args, **kwargs)
        self.plan_id_mapping: Dict[str, str] = {}
        self.migration_run: Optional[Any] = None
        self.stats: Dict[str, int] = {}
        self.lost_data_records = []
        self.lost_field_values: Dict[str, set] = {}

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

        self.stdout.write(self.get_migration_start_message())

        # Get system user for soft-delete operations
        system_user = get_system_user()

        # Create migration run record
        self.migration_run = self.create_migration_run(system_user, dry_run, hard_delete)
        self.stdout.write(f"Created migration run record: {self.migration_run.id}")

        try:
            with set_actor(system_user):
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
                self.update_migration_run_success(dry_run)

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

    def _get_plan_mapping(self, ts_real: TrafficSignReal, dry_run: bool) -> tuple[Any, bool]:
        """Get plan mapping for a TrafficSignReal."""
        plan_id = None
        plan_mapping_found = False

        if ts_real.traffic_sign_plan_id:
            plan_id = self.plan_id_mapping.get(str(ts_real.traffic_sign_plan_id))
            plan_mapping_found = plan_id is not None
            if plan_id and not dry_run:
                self.stdout.write(f"    → Mapped plan: {ts_real.traffic_sign_plan_id} → {plan_id}")

        return plan_id, plan_mapping_found

    def _delete_original_traffic_sign_real(self, ts_real: TrafficSignReal, hard_delete: bool, system_user: Any) -> None:
        """Delete or soft-delete the original TrafficSignReal."""
        if hard_delete:
            ts_real.delete()
        else:
            ts_real.soft_delete(system_user)

    def _update_device_type_target_models(self, dry_run: bool) -> None:
        """Update device type target_model for migration codes."""
        self.stdout.write("\n=== Updating device type target_model ===")

        device_codes = self.get_device_codes()
        device_types = TrafficControlDeviceType.objects.filter(code__in=device_codes)
        self.stats["device_types_updated"] = device_types.count()

        self.stdout.write(f"Found {self.stats['device_types_updated']} device types to update")

        if not dry_run:
            target_model = self.get_target_device_type_model()
            updated = device_types.update(target_model=target_model)
            self.stdout.write(f"  ✓ Updated {updated} device type(s)")
        else:
            for dt in device_types:
                self.stdout.write(f"  Would update: {dt.code} → {self.get_target_device_type_model().value}")

    def _output_report(self, dry_run: bool) -> None:
        """Output comprehensive migration report."""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("MIGRATION REPORT"))
        self.stdout.write("=" * 80)

        # Output migration-specific report
        self.output_migration_specific_report()

        # Device types
        self.stdout.write("\n🔧 Device Types:")
        self.stdout.write(f"  • Target model updated: {self.stats['device_types_updated']}")

        # Output additional warnings if any
        self.output_additional_warnings()

        # Lost data summary
        if self.lost_data_records and not dry_run:
            self.stdout.write(f"\n📝 Lost field data recorded: {len(self.lost_data_records)} entries")
            self._save_lost_data_report()

        self.stdout.write("\n" + "=" * 80)

    def _save_lost_data_report(self) -> None:
        """Save lost field data to a CSV file in agent_docs."""
        agent_docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "agent_docs",
        )
        os.makedirs(agent_docs_dir, exist_ok=True)

        filename = self.get_lost_data_report_filename()
        filepath = os.path.join(agent_docs_dir, filename)

        with open(filepath, "w") as f:
            f.write("object_type,object_id,field_name,field_value\n")
            for record in self.lost_data_records:
                f.write(f"{record}\n")

        self.stdout.write(f"  → Saved to: {filepath}")

    def _generate_unique_source_name(self, original_source_name: Optional[str]) -> str:
        """Generate unique source name for migration."""
        migration_suffix = f"_migrated_run_{self.migration_run.id}"
        return f"{original_source_name or 'unknown'}{migration_suffix}"

    def _migrate_files(
        self, source_files_queryset: Any, target_file_model: Any, target_field_name: str, target_object: Any
    ) -> int:
        """Migrate files from source to target."""
        file_count = source_files_queryset.count()
        for file_obj in source_files_queryset:
            target_file_model.objects.create(file=file_obj.file, **{target_field_name: target_object})
        return file_count

    def _get_plan_field_tracking_kwargs(self, ts_plan: TrafficSignPlan) -> Dict[str, Any]:
        """Return the 14 common had_* field tracking kwargs for a TrafficSignPlan.

        Args:
            ts_plan (TrafficSignPlan): The source plan object.

        Returns:
            Dict[str, Any]: Keyword arguments for the migration record model.
        """
        return {
            "had_height": ts_plan.height is not None,
            "had_size": ts_plan.size is not None,
            "had_direction": ts_plan.direction is not None,
            "had_reflection_class": ts_plan.reflection_class is not None,
            "had_surface_class": ts_plan.surface_class is not None,
            "had_mount_type": ts_plan.mount_type is not None,
            "had_road_name": bool(ts_plan.road_name),
            "had_lane_number": ts_plan.lane_number is not None,
            "had_lane_type": ts_plan.lane_type is not None,
            "had_location_specifier": ts_plan.location_specifier is not None,
            "had_validity_period_start": ts_plan.validity_period_start is not None,
            "had_validity_period_end": ts_plan.validity_period_end is not None,
            "had_source_name": bool(ts_plan.source_name),
            "had_source_id": bool(ts_plan.source_id),
        }

    def _get_real_field_tracking_kwargs(self, ts_real: TrafficSignReal) -> Dict[str, Any]:
        """Return the 14 common had_* field tracking kwargs for a TrafficSignReal.

        Args:
            ts_real (TrafficSignReal): The source real object.

        Returns:
            Dict[str, Any]: Keyword arguments for the migration record model.
        """
        return {
            "had_height": ts_real.height is not None,
            "had_size": ts_real.size is not None,
            "had_direction": ts_real.direction is not None,
            "had_reflection_class": ts_real.reflection_class is not None,
            "had_surface_class": ts_real.surface_class is not None,
            "had_mount_type": ts_real.mount_type is not None,
            "had_road_name": bool(ts_real.road_name),
            "had_lane_number": ts_real.lane_number is not None,
            "had_lane_type": ts_real.lane_type is not None,
            "had_location_specifier": ts_real.location_specifier is not None,
            "had_validity_period_start": ts_real.validity_period_start is not None,
            "had_validity_period_end": ts_real.validity_period_end is not None,
            "had_source_name": bool(ts_real.source_name),
            "had_source_id": bool(ts_real.source_id),
        }

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    def get_migration_start_message(self) -> str:
        """Get the migration start message."""
        pass

    @abstractmethod
    def create_migration_run(self, system_user: Any, dry_run: bool, hard_delete: bool) -> Any:
        """Create migration run record."""
        pass

    @abstractmethod
    def update_migration_run_success(self, dry_run: bool) -> None:
        """Update migration run with success status and statistics."""
        pass

    @abstractmethod
    def get_device_codes(self) -> list:
        """Get device codes to migrate."""
        pass

    @abstractmethod
    def get_target_device_type_model(self) -> DeviceTypeTargetModel:
        """Get target device type model enum."""
        pass

    @abstractmethod
    def _migrate_traffic_sign_plans(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignPlan objects."""
        pass

    @abstractmethod
    def _migrate_traffic_sign_reals(self, dry_run: bool, hard_delete: bool, system_user: Any) -> None:
        """Migrate TrafficSignReal objects."""
        pass

    @abstractmethod
    def output_migration_specific_report(self) -> None:
        """Output migration-specific parts of the report."""
        pass

    @abstractmethod
    def output_additional_warnings(self) -> None:
        """Output any additional warnings specific to the migration."""
        pass

    @abstractmethod
    def get_lost_data_report_filename(self) -> str:
        """Get filename for lost data report."""
        pass
