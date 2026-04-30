"""Tests for cleanup_migrated_traffic_signs management command."""
import uuid
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from traffic_control.constants import SIGNPOST_CODES, TICKET_MACHINE_CODES
from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models.additional_sign import AdditionalSignPlan, AdditionalSignReal
from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)
from traffic_control.models.ticket_machine_migration import (
    TicketMachineMigrationPlanRecord,
    TicketMachineMigrationRealRecord,
    TicketMachineMigrationRun,
)
from traffic_control.models.traffic_sign import TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from users.utils import get_system_user

CMD = "cleanup_migrated_traffic_signs"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def system_user(db):
    """Return or create the system user required by migration commands.

    Args:
        db: pytest-django database fixture.

    Returns:
        User: The system user instance.
    """
    return get_system_user()


@pytest.fixture
def ticket_machine_device_type(db):
    """Create a single ticket-machine device type.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: Device type with code from TICKET_MACHINE_CODES.
    """
    return TrafficControlDeviceTypeFactory(
        code=TICKET_MACHINE_CODES[0],
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
    )


@pytest.fixture
def signpost_device_type(db):
    """Create a single signpost device type.

    Args:
        db: pytest-django database fixture.

    Returns:
        TrafficControlDeviceType: Device type with code from SIGNPOST_CODES.
    """
    return TrafficControlDeviceTypeFactory(
        code=SIGNPOST_CODES[0],
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
    )


def _make_ticket_machine_run(user, *, dry_run: bool = False, hard_delete: bool = False) -> TicketMachineMigrationRun:
    """Create a TicketMachineMigrationRun with sensible defaults.

    Args:
        user: The User to set as executed_by.
        dry_run (bool): Whether to mark as dry run.
        hard_delete (bool): Whether to mark as hard-delete mode.

    Returns:
        TicketMachineMigrationRun: The created run instance.
    """
    return TicketMachineMigrationRun.objects.create(
        executed_by=user,
        dry_run=dry_run,
        hard_delete=hard_delete,
        success=True,
        completed_at=timezone.now(),
    )


def _make_signpost_run(user, *, dry_run: bool = False, hard_delete: bool = False) -> SignpostMigrationRun:
    """Create a SignpostMigrationRun with sensible defaults.

    Args:
        user: The User to set as executed_by.
        dry_run (bool): Whether to mark as dry run.
        hard_delete (bool): Whether to mark as hard-delete mode.

    Returns:
        SignpostMigrationRun: The created run instance.
    """
    return SignpostMigrationRun.objects.create(
        executed_by=user,
        dry_run=dry_run,
        hard_delete=hard_delete,
        success=True,
        completed_at=timezone.now(),
    )


def _soft_delete_plan(plan: TrafficSignPlan, user) -> TrafficSignPlan:
    """Soft-delete a plan and return it refreshed from the database.

    Args:
        plan (TrafficSignPlan): The plan instance to soft-delete.
        user: The user to record as the deleter.

    Returns:
        TrafficSignPlan: Refreshed plan with is_active=False.
    """
    plan.soft_delete(user)
    plan.refresh_from_db()
    return plan


def _soft_delete_real(real: TrafficSignReal, user) -> TrafficSignReal:
    """Soft-delete a real and return it refreshed from the database.

    Args:
        real (TrafficSignReal): The real instance to soft-delete.
        user: The user to record as the deleter.

    Returns:
        TrafficSignReal: Refreshed real with is_active=False.
    """
    real.soft_delete(user)
    real.refresh_from_db()
    return real


# ── Ticket machine plan tests ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_hard_deletes_ticket_machine_plans(system_user, ticket_machine_device_type):
    """Plans soft-deleted by ticket machine migration are hard-deleted by cleanup.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    run = _make_ticket_machine_run(system_user)
    new_id = uuid.uuid4()
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_traffic_sign_plan=plan,
        original_id=plan_id,
        new_id=new_id,
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert not TrafficSignPlan.objects.filter(id=plan_id).exists()


@pytest.mark.django_db
def test_cleanup_dry_run_skips_ticket_machine_plans(system_user, ticket_machine_device_type):
    """Dry-run mode reports candidates without hard-deleting ticket machine plans.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_traffic_sign_plan=plan,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    out = StringIO()
    call_command(CMD, "--dry-run", stdout=out)

    assert TrafficSignPlan.objects.filter(id=plan_id).exists()
    assert "DRY RUN" in out.getvalue()


# ── Ticket machine real tests ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_hard_deletes_ticket_machine_reals(system_user, ticket_machine_device_type):
    """Reals soft-deleted by ticket machine migration are hard-deleted by cleanup.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    real = TrafficSignRealFactory(device_type=ticket_machine_device_type)
    real_id = real.id
    _soft_delete_real(real, system_user)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationRealRecord.objects.create(
        migration_run=run,
        original_traffic_sign_real=real,
        original_id=real_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert not TrafficSignReal.objects.filter(id=real_id).exists()


# ── Signpost plan tests ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_hard_deletes_signpost_plans(system_user, signpost_device_type):
    """Plans soft-deleted by signpost migration are hard-deleted by cleanup.

    Args:
        system_user: The system user fixture.
        signpost_device_type: A signpost device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=signpost_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    run = _make_signpost_run(system_user)
    SignpostMigrationPlanRecord.objects.create(
        migration_run=run,
        original_traffic_sign_plan=plan,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=signpost_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert not TrafficSignPlan.objects.filter(id=plan_id).exists()


@pytest.mark.django_db
def test_cleanup_hard_deletes_signpost_reals(system_user, signpost_device_type):
    """Reals soft-deleted by signpost migration are hard-deleted by cleanup.

    Args:
        system_user: The system user fixture.
        signpost_device_type: A signpost device type fixture.

    Returns:
        None
    """
    real = TrafficSignRealFactory(device_type=signpost_device_type)
    real_id = real.id
    _soft_delete_real(real, system_user)

    run = _make_signpost_run(system_user)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_traffic_sign_real=real,
        original_id=real_id,
        new_id=uuid.uuid4(),
        device_type_code=signpost_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert not TrafficSignReal.objects.filter(id=real_id).exists()


# ── Exclusion tests ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_excludes_hard_delete_run_records(system_user, ticket_machine_device_type):
    """Records from hard-delete runs are not considered for cleanup.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    hard_delete_run = _make_ticket_machine_run(system_user, hard_delete=True)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=hard_delete_run,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    # Plan is still present (soft-deleted but not hard-deleted by cleanup)
    assert TrafficSignPlan.objects.filter(id=plan_id).exists()


@pytest.mark.django_db
def test_cleanup_excludes_dry_run_records(system_user, ticket_machine_device_type):
    """Records from dry-run migrations are not considered for cleanup.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id

    dry_run = _make_ticket_machine_run(system_user, dry_run=True)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=dry_run,
        original_id=plan_id,
        new_id=None,  # dry-run: new_id is null
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert TrafficSignPlan.objects.filter(id=plan_id).exists()


@pytest.mark.django_db
def test_cleanup_excludes_active_signs(system_user, ticket_machine_device_type):
    """Active (non-soft-deleted) traffic signs are never hard-deleted.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    # NOT soft-deleted

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    # Still active, not deleted
    assert TrafficSignPlan.objects.filter(id=plan_id, is_active=True).exists()


# ── Partial cleanup tests ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_partial_ticket_machine_run(system_user, ticket_machine_device_type):
    """--ticket-machine-run limits cleanup to the specified run.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan_a = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_b = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    _soft_delete_plan(plan_a, system_user)
    _soft_delete_plan(plan_b, system_user)

    run_1 = _make_ticket_machine_run(system_user)
    run_2 = _make_ticket_machine_run(system_user)

    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run_1,
        original_id=plan_a.id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run_2,
        original_id=plan_b.id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    call_command(CMD, f"--ticket-machine-run={run_1.id}", stdout=StringIO())

    assert not TrafficSignPlan.objects.filter(id=plan_a.id).exists()
    assert TrafficSignPlan.objects.filter(id=plan_b.id).exists()


@pytest.mark.django_db
def test_cleanup_partial_signpost_run(system_user, signpost_device_type):
    """--signpost-run limits cleanup to the specified run.

    Args:
        system_user: The system user fixture.
        signpost_device_type: A signpost device type fixture.

    Returns:
        None
    """
    plan_a = TrafficSignPlanFactory(device_type=signpost_device_type)
    plan_b = TrafficSignPlanFactory(device_type=signpost_device_type)
    _soft_delete_plan(plan_a, system_user)
    _soft_delete_plan(plan_b, system_user)

    run_1 = _make_signpost_run(system_user)
    run_2 = _make_signpost_run(system_user)

    SignpostMigrationPlanRecord.objects.create(
        migration_run=run_1,
        original_id=plan_a.id,
        new_id=uuid.uuid4(),
        device_type_code=signpost_device_type.code,
    )
    SignpostMigrationPlanRecord.objects.create(
        migration_run=run_2,
        original_id=plan_b.id,
        new_id=uuid.uuid4(),
        device_type_code=signpost_device_type.code,
    )

    call_command(CMD, f"--signpost-run={run_1.id}", stdout=StringIO())

    assert not TrafficSignPlan.objects.filter(id=plan_a.id).exists()
    assert TrafficSignPlan.objects.filter(id=plan_b.id).exists()


@pytest.mark.django_db
def test_cleanup_both_sources_in_one_invocation(system_user, ticket_machine_device_type, signpost_device_type):
    """Cleanup handles ticket machine and signpost plans in one invocation.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.
        signpost_device_type: A signpost device type fixture.

    Returns:
        None
    """
    tm_plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    sp_plan = TrafficSignPlanFactory(device_type=signpost_device_type)
    _soft_delete_plan(tm_plan, system_user)
    _soft_delete_plan(sp_plan, system_user)

    tm_run = _make_ticket_machine_run(system_user)
    sp_run = _make_signpost_run(system_user)

    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=tm_run,
        original_id=tm_plan.id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )
    SignpostMigrationPlanRecord.objects.create(
        migration_run=sp_run,
        original_id=sp_plan.id,
        new_id=uuid.uuid4(),
        device_type_code=signpost_device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    assert not TrafficSignPlan.objects.filter(id=tm_plan.id).exists()
    assert not TrafficSignPlan.objects.filter(id=sp_plan.id).exists()


# ── Output / reporting tests ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_output_reports_counts(system_user, ticket_machine_device_type):
    """Command output reports the number of candidates found.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    _soft_delete_plan(plan, system_user)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_id=plan.id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    out = StringIO()
    call_command(CMD, stdout=out)

    output = out.getvalue()
    assert "1" in output
    assert "TrafficSignPlan" in output


# ── Blocked-by-dependents tests ───────────────────────────────────────────────


@pytest.mark.django_db
def test_cleanup_skips_real_with_additional_sign_child(system_user, ticket_machine_device_type):
    """TrafficSignReal with an AdditionalSignReal child is skipped with a warning.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    real = TrafficSignRealFactory(device_type=ticket_machine_device_type)
    real_id = real.id
    _soft_delete_real(real, system_user)

    additional = AdditionalSignRealFactory(parent=real)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationRealRecord.objects.create(
        migration_run=run,
        original_traffic_sign_real=real,
        original_id=real_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    out = StringIO()
    call_command(CMD, stdout=out)

    assert TrafficSignReal.objects.filter(id=real_id).exists(), "Real should NOT be deleted — it has a child"
    assert AdditionalSignReal.objects.filter(id=additional.id).exists(), "AdditionalSignReal must be untouched"
    assert "Skipping" in out.getvalue()
    assert "will be skipped" in out.getvalue()


@pytest.mark.django_db
def test_cleanup_skips_plan_with_additional_sign_child(system_user, ticket_machine_device_type):
    """TrafficSignPlan with an AdditionalSignPlan child is skipped with a warning.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    additional = AdditionalSignPlanFactory(parent=plan)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_traffic_sign_plan=plan,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    out = StringIO()
    call_command(CMD, stdout=out)

    assert TrafficSignPlan.objects.filter(id=plan_id).exists(), "Plan should NOT be deleted — it has a child"
    assert AdditionalSignPlan.objects.filter(id=additional.id).exists(), "AdditionalSignPlan must be untouched"
    assert "Skipping" in out.getvalue()
    assert "will be skipped" in out.getvalue()


@pytest.mark.django_db
def test_cleanup_dry_run_reports_skipped_count(system_user, ticket_machine_device_type):
    """Dry-run reports the number of instances that would be skipped due to protected dependents.

    Args:
        system_user: The system user fixture.
        ticket_machine_device_type: A ticket-machine device type fixture.

    Returns:
        None
    """
    plan = TrafficSignPlanFactory(device_type=ticket_machine_device_type)
    plan_id = plan.id
    _soft_delete_plan(plan, system_user)

    AdditionalSignPlanFactory(parent=plan)

    run = _make_ticket_machine_run(system_user)
    TicketMachineMigrationPlanRecord.objects.create(
        migration_run=run,
        original_traffic_sign_plan=plan,
        original_id=plan_id,
        new_id=uuid.uuid4(),
        device_type_code=ticket_machine_device_type.code,
    )

    out = StringIO()
    call_command(CMD, "--dry-run", stdout=out)

    output = out.getvalue()
    assert TrafficSignPlan.objects.filter(id=plan_id).exists(), "Dry-run must not delete anything"
    assert "Skipping" in output
    assert "will be skipped" in output
    assert "DRY RUN" in output
