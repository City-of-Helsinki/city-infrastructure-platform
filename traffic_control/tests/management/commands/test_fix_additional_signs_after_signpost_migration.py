"""Tests for fix_additional_signs_after_signpost_migration management command."""
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from traffic_control.models.signpost_migration import (
    SignpostMigrationPlanRecord,
    SignpostMigrationRealRecord,
    SignpostMigrationRun,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from users.utils import get_system_user

CMD = "fix_additional_signs_after_signpost_migration"


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def system_user(db):
    """Return or create the system user.

    Args:
        db: pytest-django database fixture.

    Returns:
        User: The system user instance.
    """
    return get_system_user()


@pytest.fixture
def completed_at(db):
    """Return a fixed timezone-aware datetime used as migration completed_at.

    Args:
        db: pytest-django database fixture.

    Returns:
        datetime: A fixed aware datetime.
    """
    return timezone.now()


def _make_signpost_run(user, completed_at, *, dry_run: bool = False) -> SignpostMigrationRun:
    """Create a successful, non-hard-delete SignpostMigrationRun.

    Args:
        user: The User to set as executed_by.
        completed_at (datetime): The completed_at timestamp to set.
        dry_run (bool): Whether to mark as dry run.

    Returns:
        SignpostMigrationRun: The created run instance.
    """
    return SignpostMigrationRun.objects.create(
        executed_by=user,
        dry_run=dry_run,
        hard_delete=False,
        success=True,
        completed_at=completed_at,
    )


def _soft_delete_sign(sign, user, deleted_at):
    """Manually soft-delete a sign at a specific timestamp.

    Args:
        sign: The AdditionalSignPlan or AdditionalSignReal instance.
        user: The user to record as the deleter.
        deleted_at (datetime): The deleted_at timestamp to set.

    Returns:
        The refreshed, soft-deleted sign instance.
    """
    sign.soft_delete(user)
    # Override deleted_at to simulate it happened at migration time
    type(sign).objects.filter(pk=sign.pk).update(deleted_at=deleted_at)
    sign.refresh_from_db()
    return sign


# ── Plan restore tests ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_restores_cascade_deleted_additional_sign_plan(system_user, completed_at):
    """Cascade-soft-deleted AdditionalSignPlan is restored and re-parented to SignpostPlan.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_plan = TrafficSignPlanFactory()
    signpost_plan = SignpostPlanFactory()
    additional = AdditionalSignPlanFactory(parent=traffic_sign_plan)
    _soft_delete_sign(additional, system_user, completed_at)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationPlanRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_plan.id,
        new_id=signpost_plan.id,
        new_signpost_plan=signpost_plan,
        device_type_code=traffic_sign_plan.device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    additional.refresh_from_db()
    assert additional.is_active is True
    assert additional.deleted_at is None
    assert additional.signpost_plan_id == signpost_plan.id
    assert additional.parent_id is None  # cleared when re-parented to signpost


@pytest.mark.django_db
def test_fix_dry_run_does_not_restore_additional_sign_plan(system_user, completed_at):
    """Dry-run mode reports candidates without making changes to AdditionalSignPlan.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_plan = TrafficSignPlanFactory()
    signpost_plan = SignpostPlanFactory()
    additional = AdditionalSignPlanFactory(parent=traffic_sign_plan)
    _soft_delete_sign(additional, system_user, completed_at)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationPlanRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_plan.id,
        new_id=signpost_plan.id,
        new_signpost_plan=signpost_plan,
        device_type_code=traffic_sign_plan.device_type.code,
    )

    out = StringIO()
    call_command(CMD, "--dry-run", stdout=out)

    additional.refresh_from_db()
    assert additional.is_active is False, "Dry-run must not restore the sign"
    assert "Would restore" in out.getvalue()
    assert "DRY RUN" in out.getvalue()


# ── Real restore tests ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_restores_cascade_deleted_additional_sign_real(system_user, completed_at):
    """Cascade-soft-deleted AdditionalSignReal is restored and re-parented to SignpostReal.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    _soft_delete_sign(additional, system_user, completed_at)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    additional.refresh_from_db()
    assert additional.is_active is True
    assert additional.deleted_at is None
    assert additional.signpost_real_id == signpost_real.id


@pytest.mark.django_db
def test_fix_dry_run_does_not_restore_additional_sign_real(system_user, completed_at):
    """Dry-run mode reports candidates without making changes to AdditionalSignReal.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    _soft_delete_sign(additional, system_user, completed_at)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    out = StringIO()
    call_command(CMD, "--dry-run", stdout=out)

    additional.refresh_from_db()
    assert additional.is_active is False, "Dry-run must not restore the sign"
    assert "Would restore" in out.getvalue()


# ── Time-tolerance tests ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_skips_sign_deleted_outside_time_window(system_user, completed_at):
    """Signs deleted well before the migration window are not restored.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    # Deleted 10 minutes before the migration — outside the default 120s window
    far_before = completed_at - timedelta(minutes=10)
    _soft_delete_sign(additional, system_user, far_before)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    call_command(CMD, stdout=StringIO())

    additional.refresh_from_db()
    assert additional.is_active is False, "Sign outside tolerance window must not be restored"


@pytest.mark.django_db
def test_fix_respects_custom_time_tolerance(system_user, completed_at):
    """Signs within a custom --time-tolerance-seconds window are restored.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    # Deleted 3 minutes before, within a 300s custom window
    _soft_delete_sign(additional, system_user, completed_at - timedelta(minutes=3))

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    call_command(CMD, "--time-tolerance-seconds=300", stdout=StringIO())

    additional.refresh_from_db()
    assert additional.is_active is True


# ── Migration-run filtering tests ──────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_limits_to_specific_migration_run_id(system_user, completed_at):
    """--migration-run-id limits processing to the specified run only.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    ts1 = TrafficSignRealFactory()
    ts2 = TrafficSignRealFactory()
    sp1 = SignpostRealFactory()
    sp2 = SignpostRealFactory()
    add1 = AdditionalSignRealFactory(parent=ts1)
    add2 = AdditionalSignRealFactory(parent=ts2)
    _soft_delete_sign(add1, system_user, completed_at)
    _soft_delete_sign(add2, system_user, completed_at)

    run1 = _make_signpost_run(system_user, completed_at)
    run2 = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run1,
        original_id=ts1.id,
        new_id=sp1.id,
        new_signpost_real=sp1,
        device_type_code=ts1.device_type.code,
    )
    SignpostMigrationRealRecord.objects.create(
        migration_run=run2,
        original_id=ts2.id,
        new_id=sp2.id,
        new_signpost_real=sp2,
        device_type_code=ts2.device_type.code,
    )

    call_command(CMD, f"--migration-run-id={run1.id}", stdout=StringIO())

    add1.refresh_from_db()
    add2.refresh_from_db()
    assert add1.is_active is True, "add1 should be restored (in run1)"
    assert add2.is_active is False, "add2 must not be restored (in run2)"


# ── Exclusion tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_skips_dry_run_migration_records(system_user, completed_at):
    """Migration runs marked as dry_run are not processed.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    _soft_delete_sign(additional, system_user, completed_at)

    dry_run_migration = _make_signpost_run(system_user, completed_at, dry_run=True)
    SignpostMigrationRealRecord.objects.create(
        migration_run=dry_run_migration,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    out = StringIO()
    call_command(CMD, stdout=out)

    additional.refresh_from_db()
    assert additional.is_active is False
    assert "No eligible migration runs found" in out.getvalue()


@pytest.mark.django_db
def test_fix_skips_already_active_sign(system_user, completed_at):
    """Signs that are already active are reported as skipped, not re-processed.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    # Create additional sign that is already active (not soft-deleted)
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    # The active sign won't be found (filter is_active=False), so nothing is restored
    call_command(CMD, stdout=StringIO())

    additional.refresh_from_db()
    assert additional.is_active is True
    assert additional.signpost_real_id is None, "Parent should be unchanged"


# ── Output / reporting tests ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_fix_output_reports_summary(system_user, completed_at):
    """Command output contains summary counts after processing.

    Args:
        system_user: The system user fixture.
        completed_at (datetime): Fixed migration completion timestamp.

    Returns:
        None
    """
    traffic_sign_real = TrafficSignRealFactory()
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(parent=traffic_sign_real)
    _soft_delete_sign(additional, system_user, completed_at)

    run = _make_signpost_run(system_user, completed_at)
    SignpostMigrationRealRecord.objects.create(
        migration_run=run,
        original_id=traffic_sign_real.id,
        new_id=signpost_real.id,
        new_signpost_real=signpost_real,
        device_type_code=traffic_sign_real.device_type.code,
    )

    out = StringIO()
    call_command(CMD, stdout=out)

    output = out.getvalue()
    assert "Fix complete" in output
    assert "AdditionalSignReal" in output


@pytest.mark.django_db
def test_fix_reports_no_eligible_runs_when_none_exist(system_user):
    """Command reports no eligible runs when database has none.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    out = StringIO()
    call_command(CMD, stdout=out)

    assert "No eligible migration runs found" in out.getvalue()
