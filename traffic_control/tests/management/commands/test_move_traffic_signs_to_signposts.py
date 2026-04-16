"""Tests for move_traffic_signs_to_signposts management command."""
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from traffic_control.constants import SIGNPOST_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import SignpostPlan, SignpostReal
from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)
from traffic_control.tests.factories import (
    MountPlanFactory,
    MountRealFactory,
    PlanFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)

User = get_user_model()


@pytest.fixture
def signpost_device_types(db):
    """Create signpost device types."""
    device_types = []
    for code in SIGNPOST_CODES[:5]:  # Create a subset for testing
        dt = TrafficControlDeviceTypeFactory(
            code=code,
            target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
            description=f"Signpost {code}",
        )
        device_types.append(dt)
    return device_types


@pytest.mark.django_db
class TestMoveTrafficSignsToSignpostsCommand:
    """Tests for the move_traffic_signs_to_signposts management command."""

    def test_command_dry_run_no_changes(self, signpost_device_types):
        """Test that dry-run mode doesn't make any changes."""
        # Create traffic sign with signpost code
        mount = MountPlanFactory()
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        # Run command in dry-run mode
        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            "--dry-run",
            stdout=out,
        )

        # Verify no changes
        assert (
            TrafficSignPlanFactory._meta.model.objects.filter(
                device_type__code__in=SIGNPOST_CODES,
                is_active=True,
            ).count()
            == 1
        )
        assert SignpostPlan.objects.count() == 0
        signpost_device_types[0].refresh_from_db()
        assert signpost_device_types[0].target_model == DeviceTypeTargetModel.TRAFFIC_SIGN

        # Verify migration run was created
        assert SignpostMigrationRun.objects.count() == 1
        run = SignpostMigrationRun.objects.first()
        assert run.dry_run is True
        assert run.success is True
        assert run.plans_processed == 1

    def test_command_migrates_plan(self, signpost_device_types):
        """Test basic migration of a traffic sign plan to signpost plan."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
            height=250,
            size="L",
            direction=90,
            value=10.5,
            txt="Test text",
            source_name="test_source",
            source_id="12345",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify migration
        ts_plan.refresh_from_db()
        assert ts_plan.is_active is False
        assert SignpostPlan.objects.count() == 1

        new_plan = SignpostPlan.objects.first()
        assert new_plan.device_type == signpost_device_types[0]
        assert new_plan.height == 250
        assert new_plan.size.value == "L"
        assert new_plan.direction == 90
        assert new_plan.value == 10.5
        assert new_plan.txt == "Test text"
        assert new_plan.mount_plan == mount
        assert new_plan.plan == plan
        assert "_migrated_run_" in new_plan.source_name
        assert "test_source" in new_plan.source_name

        # Verify device type updated
        signpost_device_types[0].refresh_from_db()
        assert signpost_device_types[0].target_model == DeviceTypeTargetModel.SIGNPOST

        # Verify migration tracking
        assert SignpostMigrationRun.objects.count() == 1
        run = SignpostMigrationRun.objects.first()
        assert run.success is True
        assert run.plans_processed == 1
        assert run.plans_migrated == 1

    def test_command_migrates_real(self, signpost_device_types):
        """Test basic migration of a traffic sign real to signpost real."""
        mount = MountRealFactory()
        ts_real = TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount,
            height=200,
            manufacturer="Test Manufacturer",
            scanned_at="2026-01-15T10:30:00Z",
            attachment_url="https://example.com/attachment.pdf",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify migration
        ts_real.refresh_from_db()
        assert ts_real.is_active is False
        assert SignpostReal.objects.count() == 1

        new_real = SignpostReal.objects.first()
        assert new_real.device_type == signpost_device_types[0]
        assert new_real.height == 200
        assert new_real.manufacturer == "Test Manufacturer"
        assert new_real.mount_real == mount
        assert new_real.attachment_url == "https://example.com/attachment.pdf"

        # Verify tracking
        run = SignpostMigrationRun.objects.first()
        assert run.reals_processed == 1
        assert run.reals_migrated == 1

    def test_command_maps_plan_to_real(self, signpost_device_types):
        """Test that real correctly maps to migrated plan."""
        mount_plan = MountPlanFactory()
        mount_real = MountRealFactory()
        plan = PlanFactory()

        # Create plan
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount_plan,
            plan=plan,
        )

        # Create real linked to plan
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount_real,
            traffic_sign_plan=ts_plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify plan mapping
        new_real = SignpostReal.objects.first()
        new_plan = SignpostPlan.objects.first()
        assert new_real.signpost_plan == new_plan

        # Verify tracking
        real_record = SignpostMigrationRealRecord.objects.first()
        assert real_record.plan_mapping_found is True

    def test_command_real_without_plan_mapping(self, signpost_device_types):
        """Test real without plan creates signpost without plan link."""
        mount_real = MountRealFactory()
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount_real,
            traffic_sign_plan=None,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        new_real = SignpostReal.objects.first()
        assert new_real.signpost_plan is None

        # Verify tracking
        real_record = SignpostMigrationRealRecord.objects.first()
        assert real_record.plan_mapping_found is False

    def test_command_hard_delete_mode(self, signpost_device_types):
        """Test hard-delete mode permanently deletes originals."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )
        ts_plan_id = ts_plan.id

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            "--hard-delete",
            stdout=out,
        )

        # Verify original is hard-deleted
        assert not TrafficSignPlanFactory._meta.model.objects.filter(id=ts_plan_id).exists()
        assert SignpostPlan.objects.count() == 1

        run = SignpostMigrationRun.objects.first()
        assert run.hard_delete is True
        assert run.success is True
        assert run.plans_migrated == 1

        # Verify tracking records were created successfully
        assert SignpostMigrationPlanRecord.objects.count() == 1

    def test_command_soft_delete_mode(self, signpost_device_types):
        """Test soft-delete mode keeps originals."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )
        ts_plan_id = ts_plan.id

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify original is soft-deleted
        original = TrafficSignPlanFactory._meta.model.objects.get(id=ts_plan_id)
        assert original.is_active is False
        assert original.deleted_at is not None
        assert SignpostPlan.objects.count() == 1

        # Verify migration run tracked soft-delete
        run = SignpostMigrationRun.objects.first()
        assert run.hard_delete is False

    def test_command_tracks_lost_field_values(self, signpost_device_types):
        """Test that lost field values are tracked."""
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount,
            installation_id="INST123",
            installation_details="Some details",
            permit_decision_id="PERMIT456",
            rfid="RFID789",
            operation="Painting",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify lost values tracked
        run = SignpostMigrationRun.objects.first()
        assert "installation_id" in run.lost_field_values
        assert "installation_details" in run.lost_field_values
        assert "permit_decision_id" in run.lost_field_values
        assert "rfid" in run.lost_field_values
        assert "operation" in run.lost_field_values

    def test_command_preserves_attachment_url(self, signpost_device_types):
        """Test that attachment_url is preserved during migration."""
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount,
            attachment_url="https://example.com/attachment.pdf",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify attachment_url is preserved
        new_real = SignpostReal.objects.first()
        assert new_real.attachment_url == "https://example.com/attachment.pdf"

        # Verify it's NOT in lost field values
        run = SignpostMigrationRun.objects.first()
        assert "attachment_url" not in run.lost_field_values

    def test_command_creates_detailed_records(self, signpost_device_types):
        """Test that detailed migration records are created."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify plan record
        assert SignpostMigrationPlanRecord.objects.count() == 1
        plan_record = SignpostMigrationPlanRecord.objects.first()
        assert plan_record.original_id == ts_plan.id
        assert plan_record.device_type_code == signpost_device_types[0].code
        assert plan_record.had_mount_plan is True
        assert plan_record.had_plan is True

    def test_command_handles_multiple_signs(self, signpost_device_types):
        """Test migration of multiple traffic signs."""
        mount = MountPlanFactory()
        plan = PlanFactory()

        # Create 3 different signpost traffic signs
        for i in range(3):
            TrafficSignPlanFactory(
                device_type=signpost_device_types[i],
                mount_plan=mount,
                plan=plan,
            )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify all migrated
        assert SignpostPlan.objects.count() == 3
        assert SignpostMigrationPlanRecord.objects.count() == 3

        run = SignpostMigrationRun.objects.first()
        assert run.plans_processed == 3
        assert run.plans_migrated == 3

    def test_command_source_field_concatenation(self, signpost_device_types):
        """Test that source_name is concatenated with migration run ID."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
            source_name="original_source",
            source_id="original_id_123",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify source fields
        run = SignpostMigrationRun.objects.first()
        new_sign = SignpostPlan.objects.first()

        # source_name is concatenated with migration run ID
        assert f"original_source_migrated_run_{run.id}" in new_sign.source_name
        # source_id is preserved
        assert new_sign.source_id == "original_id_123"

    def test_command_updates_all_device_types(self, signpost_device_types):
        """Test that all signpost device types are updated."""
        mount = MountPlanFactory()
        plan = PlanFactory()

        # Create one sign (to trigger migration)
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Verify ALL device types updated (not just the one used)
        for dt in signpost_device_types:
            dt.refresh_from_db()
            assert dt.target_model == DeviceTypeTargetModel.SIGNPOST

        run = SignpostMigrationRun.objects.first()
        assert run.device_types_updated == len(signpost_device_types)

    def test_command_handles_missing_mount(self, signpost_device_types):
        """Test migration works even without mount."""
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=None,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Should still migrate successfully
        assert SignpostPlan.objects.count() == 1
        new_sign = SignpostPlan.objects.first()
        assert new_sign.mount_plan is None

    def test_command_records_execution_time(self, signpost_device_types):
        """Test that execution time is recorded."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        run = SignpostMigrationRun.objects.first()
        assert run.started_at is not None
        assert run.completed_at is not None
        assert run.completed_at >= run.started_at

    def test_command_handles_empty_attachment_url(self, signpost_device_types):
        """Test that empty attachment_url is handled correctly."""
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount,
            attachment_url="",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        new_real = SignpostReal.objects.first()
        assert new_real.attachment_url == ""

    def test_command_tracks_real_detail_fields(self, signpost_device_types):
        """Test that real-specific fields are tracked in detail record."""
        mount = MountRealFactory()
        TrafficSignRealFactory(
            device_type=signpost_device_types[0],
            mount_real=mount,
            legacy_code="LEGACY123",
            scanned_at="2026-01-15T10:30:00Z",
            manufacturer="TestCo",
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        real_record = SignpostMigrationRealRecord.objects.first()
        assert real_record.had_legacy_code is True
        assert real_record.had_scanned_at is True
        assert real_record.had_manufacturer is True

    def test_command_handles_null_fields(self, signpost_device_types):
        """Test migration with many null/empty fields."""
        mount = MountPlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=None,
            height=None,
            size=None,
            direction=None,
            value=None,
            txt=None,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        # Should still migrate successfully
        assert SignpostPlan.objects.count() == 1
        new_plan = SignpostPlan.objects.first()
        assert new_plan.plan is None
        assert new_plan.height is None

    def test_command_preserves_user_fields(self, signpost_device_types):
        """Test that created_by and updated_by are preserved."""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Create a user for the sign
        user = User.objects.create_user(username="testuser", email="test@example.com")

        mount = MountPlanFactory()
        plan = PlanFactory()
        ts_plan = TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )
        # Set created_by and updated_by
        TrafficSignPlanFactory._meta.model.objects.filter(id=ts_plan.id).update(
            created_by=user,
            updated_by=user,
        )
        ts_plan.refresh_from_db()

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        new_plan = SignpostPlan.objects.first()
        # User fields should be preserved
        assert new_plan.created_by == user
        assert new_plan.updated_by == user

    def test_command_output_contains_summary(self, signpost_device_types):
        """Test that command output contains a summary report."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            stdout=out,
        )

        output = out.getvalue()
        assert "MIGRATION REPORT" in output
        assert "TrafficSignPlan Migration" in output
        assert "Processed:" in output
        assert "Migrated:" in output

    def test_command_dry_run_output(self, signpost_device_types):
        """Test that dry-run output indicates no changes."""
        mount = MountPlanFactory()
        plan = PlanFactory()
        TrafficSignPlanFactory(
            device_type=signpost_device_types[0],
            mount_plan=mount,
            plan=plan,
        )

        out = StringIO()
        call_command(
            "move_traffic_signs_to_signposts",
            "--dry-run",
            stdout=out,
        )

        output = out.getvalue()
        assert "DRY RUN MODE" in output
        assert "DRY RUN COMPLETE" in output
