"""Tests for ticket machine migration admin functionality."""
import uuid

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone

from traffic_control.admin.ticket_machine_migration import (
    TicketMachineMigrationPlanRecordAdmin,
    TicketMachineMigrationRealRecordAdmin,
    TicketMachineMigrationRunAdmin,
)
from traffic_control.models.ticket_machine_migration import (
    TicketMachineMigrationPlanRecord,
    TicketMachineMigrationRealRecord,
    TicketMachineMigrationRun,
)

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_superuser(username="admin", email="admin@test.com", password="password")


@pytest.fixture
def request_factory():
    """Create a request factory."""
    return RequestFactory()


@pytest.fixture
def admin_request(request_factory, admin_user):
    """Create an admin request with authenticated user and message middleware."""
    request = request_factory.get("/admin/")
    request.user = admin_user
    # Add message middleware support
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.fixture
def test_uuid():
    """Generate a test UUID."""
    return uuid.uuid4()


@pytest.fixture
def migration_run(admin_user):
    """Create a test migration run."""
    return TicketMachineMigrationRun.objects.create(
        executed_by=admin_user,
        dry_run=False,
        hard_delete=False,
        plans_processed=10,
        plans_migrated=8,
        plans_with_parent=5,
        plans_without_parent=3,
        reals_processed=20,
        reals_migrated=18,
        reals_with_parent=12,
        reals_without_parent=6,
        device_types_updated=6,
        success=True,
        completed_at=timezone.now(),
        lost_field_values={
            "value": ["10", "20", "30"],
            "txt": ["Info text"],
            "double_sided": [],
            "peak_fastened": ["True"],
            "affect_area": [],
        },
    )


@pytest.fixture
def failed_migration_run(admin_user):
    """Create a failed migration run."""
    return TicketMachineMigrationRun.objects.create(
        executed_by=admin_user,
        dry_run=False,
        hard_delete=False,
        success=False,
        error_message="Test error message",
        lost_field_values={},
    )


@pytest.fixture
def dry_run_migration(admin_user):
    """Create a dry-run migration."""
    return TicketMachineMigrationRun.objects.create(
        executed_by=admin_user,
        dry_run=True,
        hard_delete=False,
        success=True,
        completed_at=timezone.now(),
        lost_field_values={
            "value": [],
            "txt": [],
            "double_sided": [],
            "peak_fastened": [],
            "affect_area": [],
        },
    )


@pytest.mark.django_db
class TestTicketMachineMigrationRunAdmin:
    """Tests for TicketMachineMigrationRunAdmin."""

    def test_has_add_permission(self, admin_request):
        """Test that adding migration runs is disabled."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_add_permission(admin_request) is False

    def test_has_delete_permission_successful_migration(self, admin_request, migration_run):
        """Test that successful non-dry-run migrations cannot be deleted."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, migration_run) is False

    def test_has_delete_permission_failed_migration(self, admin_request, failed_migration_run):
        """Test that failed migrations can be deleted."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, failed_migration_run) is True

    def test_has_delete_permission_dry_run(self, admin_request, dry_run_migration):
        """Test that dry-run migrations can be deleted."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, dry_run_migration) is True

    def test_mode_display_dry_run(self, dry_run_migration):
        """Test mode display for dry-run migration."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(dry_run_migration)
        assert "DRY RUN" in result
        assert "#ffc107" in result  # Yellow background

    def test_mode_display_hard_delete(self, admin_user):
        """Test mode display for hard-delete migration."""
        run = TicketMachineMigrationRun.objects.create(
            executed_by=admin_user, dry_run=False, hard_delete=True, success=True
        )
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(run)
        assert "HARD DELETE" in result
        assert "#dc3545" in result  # Red background

    def test_mode_display_soft_delete(self, migration_run):
        """Test mode display for soft-delete migration."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(migration_run)
        assert "SOFT DELETE" in result
        assert "#28a745" in result  # Green background

    def test_status_display_dry_run_success(self, dry_run_migration):
        """Test status display for successful dry-run."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(dry_run_migration)
        assert "DRY RUN SUCCESS" in result
        assert "#17a2b8" in result  # Cyan background

    def test_status_display_success(self, migration_run):
        """Test status display for successful migration."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(migration_run)
        assert "SUCCESS" in result
        assert "#28a745" in result  # Green background

    def test_status_display_failed(self, failed_migration_run):
        """Test status display for failed migration."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(failed_migration_run)
        assert "FAILED" in result
        assert "#dc3545" in result  # Red background

    def test_status_display_in_progress(self, admin_user):
        """Test status display for in-progress migration."""
        run = TicketMachineMigrationRun.objects.create(
            executed_by=admin_user, dry_run=False, hard_delete=False, success=False
        )
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(run)
        assert "IN PROGRESS" in result
        assert "#6c757d" in result  # Gray background

    def test_duration_display_with_time(self, migration_run):
        """Test duration display when migration is completed."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.duration(migration_run)
        assert result != "-"
        assert "s" in result  # Should have seconds

    def test_duration_display_without_completion(self, admin_user):
        """Test duration display when migration is not completed."""
        run = TicketMachineMigrationRun.objects.create(executed_by=admin_user, dry_run=False, hard_delete=False)
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.duration(run)
        assert result == "-"

    def test_plans_summary(self, migration_run):
        """Test plans summary display."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.plans_summary(migration_run)
        assert "8/10" in result  # migrated/processed
        assert "5 with parent" in result
        assert "3 without parent" in result

    def test_plans_summary_no_plans(self, admin_user):
        """Test plans summary when no plans processed."""
        run = TicketMachineMigrationRun.objects.create(executed_by=admin_user, plans_processed=0, plans_migrated=0)
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.plans_summary(run)
        assert result == "-"

    def test_reals_summary(self, migration_run):
        """Test reals summary display."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.reals_summary(migration_run)
        assert "18/20" in result  # migrated/processed
        assert "12 with parent" in result
        assert "6 without parent" in result

    def test_lost_field_values_display_with_data(self, migration_run):
        """Test lost field values display when data exists."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.lost_field_values_display(migration_run)

        assert "value" in result
        assert "10, 20, 30" in result
        assert "3 unique" in result

        assert "txt" in result
        assert "Info text" in result
        assert "1 unique" in result

        assert "double_sided" in result
        assert "No data lost" in result

        assert "peak_fastened" in result
        assert "True" in result
        assert "1 unique" in result

        assert "affect_area" in result
        assert "No data lost" in result

    def test_lost_field_values_display_all_empty(self, dry_run_migration):
        """Test lost field values display when all fields are empty."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.lost_field_values_display(dry_run_migration)

        assert "value" in result
        assert "txt" in result
        assert "double_sided" in result
        assert "peak_fastened" in result
        assert "affect_area" in result
        assert result.count("No data lost") == 5  # All 5 fields should show "No data lost"

    def test_lost_field_values_display_no_tracking(self, admin_user):
        """Test lost field values display when no tracking exists."""
        run = TicketMachineMigrationRun.objects.create(executed_by=admin_user, lost_field_values={})
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.lost_field_values_display(run)

        assert result.count("No data lost") == 5  # All 5 fields should show "No data lost"

    def test_delete_selected_migration_runs_action(self, admin_request, dry_run_migration, migration_run):
        """Test bulk delete action respects permissions."""
        admin = TicketMachineMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        queryset = TicketMachineMigrationRun.objects.filter(id__in=[dry_run_migration.id, migration_run.id])

        admin.delete_selected_migration_runs(admin_request, queryset)

        # Dry-run should be deleted
        assert not TicketMachineMigrationRun.objects.filter(id=dry_run_migration.id).exists()

        # Successful non-dry-run should remain
        assert TicketMachineMigrationRun.objects.filter(id=migration_run.id).exists()


@pytest.mark.django_db
class TestTicketMachineMigrationPlanRecordAdmin:
    """Tests for TicketMachineMigrationPlanRecordAdmin."""

    def test_has_add_permission(self, admin_request):
        """Test that adding plan records is disabled."""
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        assert admin.has_add_permission(admin_request) is False

    def test_has_delete_permission_dry_run(self, admin_request, dry_run_migration, test_uuid):
        """Test that records from dry-run migrations can be deleted."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        assert admin.has_delete_permission(admin_request, record) is True

    def test_has_delete_permission_failed(self, admin_request, failed_migration_run, test_uuid):
        """Test that records from failed migrations can be deleted."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=failed_migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        assert admin.has_delete_permission(admin_request, record) is True

    def test_has_delete_permission_successful(self, admin_request, migration_run, test_uuid):
        """Test that records from successful migrations cannot be deleted."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        assert admin.has_delete_permission(admin_request, record) is False

    def test_original_id_short(self, migration_run):
        """Test original ID is shortened."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id="12345678-1234-1234-1234-123456789012",
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.original_id_short(record)
        assert result == "12345678..."

    def test_new_id_short_with_id(self, migration_run, test_uuid):
        """Test new ID is shortened when present."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            new_id="87654321-4321-4321-4321-210987654321",
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.new_id_short(record)
        assert result == "87654321..."

    def test_new_id_short_without_id(self, migration_run, test_uuid):
        """Test new ID display when not present."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.new_id_short(record)
        assert result == "-"

    def test_parent_status_found(self, migration_run, test_uuid):
        """Test parent status when parent is found."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            parent_found=True,
            parent_sign_code="E2",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.parent_status(record)
        assert "E2" in result
        assert "#28a745" in result  # Green color

    def test_parent_status_multiple_found(self, migration_run, test_uuid):
        """Test parent status when multiple parents found."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            parent_found=True,
            parent_sign_code="521",
            multiple_parents_found=True,
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.parent_status(record)
        assert "521" in result
        assert "⚠" in result  # Warning symbol

    def test_parent_status_not_found(self, migration_run, test_uuid):
        """Test parent status when no parent found."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            parent_found=False,
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.parent_status(record)
        assert "No parent" in result

    def test_field_population_summary(self, migration_run, test_uuid):
        """Test field population summary calculation."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            had_height=True,
            had_size=True,
            had_direction=True,
            # Rest are False, so 3/16
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.field_population_summary(record)
        assert "3/16" in result
        assert "18%" in result  # 3/16 * 100 = 18.75, int() = 18

    def test_lost_data_summary_none(self, migration_run, test_uuid):
        """Test lost data summary when no data lost."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.lost_data_summary(record)
        assert "None" in result
        assert "#28a745" in result  # Green color

    def test_lost_data_summary_with_data(self, migration_run, test_uuid):
        """Test lost data summary when data is lost."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            lost_value="10",
            lost_txt="Info text",
            had_affect_area=True,
        )
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        result = admin.lost_data_summary(record)
        assert "value" in result
        assert "txt" in result
        assert "affect_area" in result
        assert "#ffc107" in result  # Yellow color


@pytest.mark.django_db
class TestTicketMachineMigrationRealRecordAdmin:
    """Tests for TicketMachineMigrationRealRecordAdmin."""

    def test_has_add_permission(self, admin_request):
        """Test that adding real records is disabled."""
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        assert admin.has_add_permission(admin_request) is False

    def test_has_delete_permission_dry_run(self, admin_request, dry_run_migration, test_uuid):
        """Test that records from dry-run migrations can be deleted."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        assert admin.has_delete_permission(admin_request, record) is True

    def test_plan_mapping_status_mapped(self, migration_run, test_uuid):
        """Test plan mapping status when plan is mapped."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            plan_mapping_found=True,
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.plan_mapping_status(record)
        assert "Mapped" in result
        assert "#28a745" in result  # Green color

    def test_plan_mapping_status_not_found(self, migration_run, test_uuid):
        """Test plan mapping status when plan not found."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            plan_mapping_found=False,
            had_traffic_sign_plan=True,
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.plan_mapping_status(record)
        assert "Not found" in result
        assert "#ffc107" in result  # Yellow color

    def test_plan_mapping_status_no_plan(self, migration_run, test_uuid):
        """Test plan mapping status when no plan existed."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            plan_mapping_found=False,
            had_traffic_sign_plan=False,
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.plan_mapping_status(record)
        assert "No plan" in result

    def test_field_population_summary_real(self, migration_run, test_uuid):
        """Test field population summary for real records."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            had_height=True,
            had_size=True,
            had_direction=True,
            had_legacy_code=True,
            had_installation_status=True,
            # 5 out of 27 fields
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.field_population_summary(record)
        assert "5/27" in result
        assert "18%" in result  # 5/27 * 100 = 18.5, int() = 18

    def test_lost_data_summary_real_with_data(self, migration_run, test_uuid):
        """Test lost data summary for real records with lost data."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            lost_value="20",
            lost_double_sided=True,
        )
        admin = TicketMachineMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.lost_data_summary(record)
        assert "value" in result
        assert "double_sided" in result
        assert "#ffc107" in result  # Yellow color
