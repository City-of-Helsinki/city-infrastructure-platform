"""Tests for ticket machine migration admin functionality."""
import uuid

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone

from traffic_control.admin.ticket_machine_migration import (
    TicketMachineMigrationPlanRecordAdmin,
    TicketMachineTrafficSignMigrationRealRecordAdmin,
    TicketMachineTrafficSignMigrationRunAdmin,
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
def staff_user_view_only(db):
    """Create a staff user with only view permissions."""
    user = User.objects.create_user(username="staff_viewer", email="staff@test.com", password="password")
    user.is_staff = True
    user.save()

    # Add view permissions for all three models
    for model in [TicketMachineMigrationRun, TicketMachineMigrationPlanRecord, TicketMachineMigrationRealRecord]:
        content_type = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.get(content_type=content_type, codename=f"view_{model._meta.model_name}")
        user.user_permissions.add(view_perm)

    return user


@pytest.fixture
def staff_user_with_delete(db):
    """Create a staff user with view and delete permissions."""
    user = User.objects.create_user(username="staff_deleter", email="staff_del@test.com", password="password")
    user.is_staff = True
    user.save()

    # Add view and delete permissions
    for model in [TicketMachineMigrationRun, TicketMachineMigrationPlanRecord, TicketMachineMigrationRealRecord]:
        content_type = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.get(content_type=content_type, codename=f"view_{model._meta.model_name}")
        delete_perm = Permission.objects.get(content_type=content_type, codename=f"delete_{model._meta.model_name}")
        user.user_permissions.add(view_perm, delete_perm)

    return user


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
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_add_permission(admin_request) is False

    def test_has_delete_permission_successful_migration(self, admin_request, migration_run):
        """Test that successful non-dry-run migrations cannot be deleted."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, migration_run) is False

    def test_has_delete_permission_failed_migration(self, admin_request, failed_migration_run):
        """Test that failed migrations can be deleted."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, failed_migration_run) is True

    def test_has_delete_permission_dry_run(self, admin_request, dry_run_migration):
        """Test that dry-run migrations can be deleted."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        assert admin.has_delete_permission(admin_request, dry_run_migration) is True

    def test_has_delete_permission_staff_view_only_fails(
        self, request_factory, staff_user_view_only, dry_run_migration
    ):
        """Test that staff user with only view permission cannot delete even dry-run migrations."""
        request = request_factory.get("/admin/")
        request.user = staff_user_view_only
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        # Even though it's a dry-run (which business logic allows), user lacks base delete permission
        assert admin.has_delete_permission(request, dry_run_migration) is False

    def test_has_delete_permission_staff_with_delete_on_dry_run(
        self, request_factory, staff_user_with_delete, dry_run_migration
    ):
        """Test that staff user with delete permission can delete dry-run migrations."""
        request = request_factory.get("/admin/")
        request.user = staff_user_with_delete
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        # Has both base delete permission AND passes business logic check
        assert admin.has_delete_permission(request, dry_run_migration) is True

    def test_has_delete_permission_staff_with_delete_on_success_fails(
        self, request_factory, staff_user_with_delete, migration_run
    ):
        """Test that staff user with delete permission still cannot delete successful migrations."""
        request = request_factory.get("/admin/")
        request.user = staff_user_with_delete
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        # Has base delete permission but fails business logic check (successful migration)
        assert admin.has_delete_permission(request, migration_run) is False

    def test_mode_display_dry_run(self, dry_run_migration):
        """Test mode display for dry-run migration."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(dry_run_migration)
        assert "DRY RUN" in result
        assert "#ffc107" in result  # Yellow background

    def test_mode_display_hard_delete(self, admin_user):
        """Test mode display for hard-delete migration."""
        run = TicketMachineMigrationRun.objects.create(
            executed_by=admin_user, dry_run=False, hard_delete=True, success=True
        )
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(run)
        assert "HARD DELETE" in result
        assert "#dc3545" in result  # Red background

    def test_mode_display_soft_delete(self, migration_run):
        """Test mode display for soft-delete migration."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.mode_display(migration_run)
        assert "SOFT DELETE" in result
        assert "#28a745" in result  # Green background

    def test_status_display_dry_run_success(self, dry_run_migration):
        """Test status display for successful dry-run."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(dry_run_migration)
        assert "DRY RUN SUCCESS" in result
        assert "#17a2b8" in result  # Cyan background

    def test_status_display_success(self, migration_run):
        """Test status display for successful migration."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(migration_run)
        assert "SUCCESS" in result
        assert "#28a745" in result  # Green background

    def test_status_display_failed(self, failed_migration_run):
        """Test status display for failed migration."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(failed_migration_run)
        assert "FAILED" in result
        assert "#dc3545" in result  # Red background

    def test_status_display_in_progress(self, admin_user):
        """Test status display for in-progress migration."""
        run = TicketMachineMigrationRun.objects.create(
            executed_by=admin_user, dry_run=False, hard_delete=False, success=False
        )
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.status_display(run)
        assert "IN PROGRESS" in result
        assert "#6c757d" in result  # Gray background

    def test_duration_display_with_time(self, migration_run):
        """Test duration display when migration is completed."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.duration(migration_run)
        assert result != "-"
        assert "s" in result  # Should have seconds

    def test_duration_display_without_completion(self, admin_user):
        """Test duration display when migration is not completed."""
        run = TicketMachineMigrationRun.objects.create(executed_by=admin_user, dry_run=False, hard_delete=False)
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.duration(run)
        assert result == "-"

    def test_plans_summary(self, migration_run):
        """Test plans summary display."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.plans_summary(migration_run)
        assert "8/10" in result  # migrated/processed
        assert "5 with parent" in result
        assert "3 without parent" in result

    def test_plans_summary_no_plans(self, admin_user):
        """Test plans summary when no plans processed."""
        run = TicketMachineMigrationRun.objects.create(executed_by=admin_user, plans_processed=0, plans_migrated=0)
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.plans_summary(run)
        assert result == "-"

    def test_reals_summary(self, migration_run):
        """Test reals summary display."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.reals_summary(migration_run)
        assert "18/20" in result  # migrated/processed
        assert "12 with parent" in result
        assert "6 without parent" in result

    def test_lost_field_values_display_with_data(self, migration_run):
        """Test lost field values display when data exists."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        result = admin.lost_field_values_display(run)

        assert result.count("No data lost") == 5  # All 5 fields should show "No data lost"

    def test_delete_queryset_respects_permissions(self, admin_request, dry_run_migration, migration_run):
        """Test delete_queryset override filters out protected records."""
        admin = TicketMachineTrafficSignMigrationRunAdmin(TicketMachineMigrationRun, AdminSite())
        queryset = TicketMachineMigrationRun.objects.filter(id__in=[dry_run_migration.id, migration_run.id])

        admin.delete_queryset(admin_request, queryset)

        # Dry-run should be deleted
        assert not TicketMachineMigrationRun.objects.filter(id=dry_run_migration.id).exists()

        # Successful non-dry-run should remain (protected by business logic)
        assert TicketMachineMigrationRun.objects.filter(id=migration_run.id).exists()


@pytest.mark.django_db
class TestTicketMachineMigrationPlanRecordAdmin:
    """Tests for TicketMachineMigrationPlanRecordAdmin."""

    def test_has_add_permission(self, admin_request):
        """Test that adding plan records is disabled."""
        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        assert admin.has_add_permission(admin_request) is False

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

    def test_has_delete_permission_staff_view_only_fails(
        self, request_factory, staff_user_view_only, dry_run_migration, test_uuid
    ):
        """Test that staff user with only view permission cannot delete plan records."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )

        request = request_factory.get("/admin/")
        request.user = staff_user_view_only
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        # Lacks base delete permission
        assert admin.has_delete_permission(request, record) is False

    def test_has_delete_permission_staff_with_delete_on_dry_run(
        self, request_factory, staff_user_with_delete, dry_run_migration, test_uuid
    ):
        """Test that staff user with delete permission can delete records from dry-run migrations."""
        record = TicketMachineMigrationPlanRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )

        request = request_factory.get("/admin/")
        request.user = staff_user_with_delete
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineMigrationPlanRecordAdmin(TicketMachineMigrationPlanRecord, AdminSite())
        # Has both base permission and passes business logic
        assert admin.has_delete_permission(request, record) is True

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
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        assert admin.has_add_permission(admin_request) is False

    def test_has_delete_permission_staff_view_only_fails(
        self, request_factory, staff_user_view_only, dry_run_migration, test_uuid
    ):
        """Test that staff user with only view permission cannot delete real records."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )

        request = request_factory.get("/admin/")
        request.user = staff_user_view_only
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        # Lacks base delete permission
        assert admin.has_delete_permission(request, record) is False

    def test_has_delete_permission_staff_with_delete_on_dry_run(
        self, request_factory, staff_user_with_delete, dry_run_migration, test_uuid
    ):
        """Test that staff user with delete permission can delete records from dry-run migrations."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=dry_run_migration,
            original_id=test_uuid,
            device_type_code="H20.91",
        )

        request = request_factory.get("/admin/")
        request.user = staff_user_with_delete
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        # Has both base permission and passes business logic
        assert admin.has_delete_permission(request, record) is True

    def test_plan_mapping_status_mapped(self, migration_run, test_uuid):
        """Test plan mapping status when plan is mapped."""
        record = TicketMachineMigrationRealRecord.objects.create(
            migration_run=migration_run,
            original_id=test_uuid,
            device_type_code="H20.91",
            plan_mapping_found=True,
        )
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
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
        admin = TicketMachineTrafficSignMigrationRealRecordAdmin(TicketMachineMigrationRealRecord, AdminSite())
        result = admin.lost_data_summary(record)
        assert "value" in result
        assert "double_sided" in result
        assert "#ffc107" in result  # Yellow color
