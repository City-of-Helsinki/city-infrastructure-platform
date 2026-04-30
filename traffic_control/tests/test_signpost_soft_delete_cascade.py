"""Tests for SignpostPlan and SignpostReal soft-delete cascade to AdditionalSign objects."""
import pytest

from traffic_control.models.signpost import SignpostPlan, SignpostReal
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    UserFactory,
)
from users.utils import get_system_user

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


@pytest.fixture()
def other_user(db):
    """Return or create a non-system user."""
    return UserFactory(username="other")


# ── SignpostPlan instance soft_delete ──────────────────────────────────────────


@pytest.mark.django_db
def test_signpost_plan_soft_delete_cascades_to_additional_sign_plan(system_user):
    """Soft-deleting a SignpostPlan instance cascades to its AdditionalSignPlan children.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    signpost_plan = SignpostPlanFactory()
    additional = AdditionalSignPlanFactory(signpost_plan=signpost_plan, parent=None)

    signpost_plan.soft_delete(system_user)

    signpost_plan.refresh_from_db()
    additional.refresh_from_db()
    assert signpost_plan.is_active is False
    assert additional.is_active is False
    assert additional.deleted_at is not None


@pytest.mark.django_db
def test_signpost_plan_soft_delete_does_not_overwrite_already_inactive_additional_sign_plans(system_user, other_user):
    """Already-inactive AdditionalSignPlan children are not re-deleted and their deleted_at is preserved.

    Args:
        system_user: The system user fixture.
        other_user: Non system user, used as original soft-deleter

    Returns:
        None
    """
    signpost_plan = SignpostPlanFactory()
    active_additional = AdditionalSignPlanFactory(signpost_plan=signpost_plan, parent=None)
    inactive_additional = AdditionalSignPlanFactory(signpost_plan=signpost_plan, parent=None)
    inactive_additional.soft_delete(other_user)
    original_deleted_at = inactive_additional.deleted_at
    original_deleted_by = inactive_additional.deleted_by

    signpost_plan.soft_delete(system_user)

    active_additional.refresh_from_db()
    inactive_additional.refresh_from_db()
    assert active_additional.is_active is False
    assert inactive_additional.deleted_at == original_deleted_at
    assert inactive_additional.deleted_by == original_deleted_by


@pytest.mark.django_db
def test_signpost_plan_soft_delete_does_not_cascade_to_unrelated_additional_sign_plan(system_user):
    """AdditionalSignPlan linked to a different SignpostPlan is not affected.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    signpost_plan = SignpostPlanFactory()
    other_signpost_plan = SignpostPlanFactory()
    other_additional = AdditionalSignPlanFactory(signpost_plan=other_signpost_plan, parent=None)

    signpost_plan.soft_delete(system_user)

    other_additional.refresh_from_db()
    assert other_additional.is_active is True


# ── SignpostReal instance soft_delete ──────────────────────────────────────────


@pytest.mark.django_db
def test_signpost_real_soft_delete_cascades_to_additional_sign_real(system_user):
    """Soft-deleting a SignpostReal instance cascades to its AdditionalSignReal children.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    signpost_real = SignpostRealFactory()
    additional = AdditionalSignRealFactory(signpost_real=signpost_real, parent=None)

    signpost_real.soft_delete(system_user)

    signpost_real.refresh_from_db()
    additional.refresh_from_db()
    assert signpost_real.is_active is False
    assert additional.is_active is False
    assert additional.deleted_at is not None


@pytest.mark.django_db
def test_signpost_real_soft_delete_does_not_overwrite_already_inactive_additional_sign_reals(system_user):
    """Already-inactive AdditionalSignReal children are not re-deleted and their deleted_at is preserved.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    signpost_real = SignpostRealFactory()
    active_additional = AdditionalSignRealFactory(signpost_real=signpost_real, parent=None)
    inactive_additional = AdditionalSignRealFactory(signpost_real=signpost_real, parent=None)
    inactive_additional.soft_delete(system_user)
    original_deleted_at = inactive_additional.deleted_at

    signpost_real.soft_delete(system_user)

    active_additional.refresh_from_db()
    inactive_additional.refresh_from_db()
    assert active_additional.is_active is False
    assert inactive_additional.deleted_at == original_deleted_at


@pytest.mark.django_db
def test_signpost_real_soft_delete_does_not_cascade_to_unrelated_additional_sign_real(system_user):
    """AdditionalSignReal linked to a different SignpostReal is not affected.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    signpost_real = SignpostRealFactory()
    other_signpost_real = SignpostRealFactory()
    other_additional = AdditionalSignRealFactory(signpost_real=other_signpost_real, parent=None)

    signpost_real.soft_delete(system_user)

    other_additional.refresh_from_db()
    assert other_additional.is_active is True


# ── SignpostPlanQuerySet bulk soft_delete ──────────────────────────────────────


@pytest.mark.django_db
def test_signpost_plan_queryset_soft_delete_cascades_to_additional_sign_plans(system_user):
    """Bulk soft-delete via queryset cascades to AdditionalSignPlan children of all plans.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    sp1 = SignpostPlanFactory()
    sp2 = SignpostPlanFactory()
    add1 = AdditionalSignPlanFactory(signpost_plan=sp1, parent=None)
    add2 = AdditionalSignPlanFactory(signpost_plan=sp2, parent=None)

    SignpostPlan.objects.filter(pk__in=[sp1.pk, sp2.pk]).soft_delete(system_user)

    for obj in [sp1, sp2, add1, add2]:
        obj.refresh_from_db()
        assert obj.is_active is False


@pytest.mark.django_db
def test_signpost_plan_queryset_soft_delete_does_not_affect_unrelated_additional_sign_plans(system_user):
    """Bulk soft-delete does not cascade to additional signs outside the queryset.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    sp_target = SignpostPlanFactory()
    sp_other = SignpostPlanFactory()
    AdditionalSignPlanFactory(signpost_plan=sp_target, parent=None)
    other_additional = AdditionalSignPlanFactory(signpost_plan=sp_other, parent=None)

    SignpostPlan.objects.filter(pk=sp_target.pk).soft_delete(system_user)

    other_additional.refresh_from_db()
    assert other_additional.is_active is True


# ── SignpostRealQuerySet bulk soft_delete ──────────────────────────────────────


@pytest.mark.django_db
def test_signpost_real_queryset_soft_delete_cascades_to_additional_sign_reals(system_user):
    """Bulk soft-delete via queryset cascades to AdditionalSignReal children of all reals.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    sr1 = SignpostRealFactory()
    sr2 = SignpostRealFactory()
    add1 = AdditionalSignRealFactory(signpost_real=sr1, parent=None)
    add2 = AdditionalSignRealFactory(signpost_real=sr2, parent=None)

    SignpostReal.objects.filter(pk__in=[sr1.pk, sr2.pk]).soft_delete(system_user)

    for obj in [sr1, sr2, add1, add2]:
        obj.refresh_from_db()
        assert obj.is_active is False


@pytest.mark.django_db
def test_signpost_real_queryset_soft_delete_does_not_affect_unrelated_additional_sign_reals(system_user):
    """Bulk soft-delete does not cascade to additional signs outside the queryset.

    Args:
        system_user: The system user fixture.

    Returns:
        None
    """
    sr_target = SignpostRealFactory()
    sr_other = SignpostRealFactory()
    AdditionalSignRealFactory(signpost_real=sr_target, parent=None)
    other_additional = AdditionalSignRealFactory(signpost_real=sr_other, parent=None)

    SignpostReal.objects.filter(pk=sr_target.pk).soft_delete(system_user)

    other_additional.refresh_from_db()
    assert other_additional.is_active is True
