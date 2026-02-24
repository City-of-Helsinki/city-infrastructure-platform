"""Tests for UserDeactivationStatus model and related signals."""

from datetime import timedelta

import pytest
from django.utils import timezone

from users.models import User, UserDeactivationStatus


@pytest.mark.django_db
def test_user_deactivation_status_creation():
    """
    Test UserDeactivationStatus model can be created.

    Verifies that a deactivation status record can be created for a user.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")
    status = UserDeactivationStatus.objects.create(user=user)

    assert status.user == user
    assert status.deactivated_at is None
    assert status.one_month_email_sent_at is None
    assert status.one_week_email_sent_at is None
    assert status.one_day_email_sent_at is None
    assert status.deactivated_at is None


@pytest.mark.django_db
def test_user_deactivation_status_string_representation():
    """
    Test UserDeactivationStatus __str__ method.

    Verifies that the string representation shows username and status.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")

    # Pending status
    status = UserDeactivationStatus.objects.create(user=user)
    assert "testuser - pending" in str(status)

    # Deactivated status
    status.deactivated_at = timezone.now()
    status.save()
    assert "testuser - deactivated" in str(status)


@pytest.mark.django_db
def test_signal_deletes_deactivation_status_on_last_login_update():
    """
    Test signal deletes UserDeactivationStatus when last_login is updated.

    Verifies that updating last_login triggers signal to delete deactivation status.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")
    UserDeactivationStatus.objects.create(user=user)

    assert hasattr(user, "deactivation_status")

    # Update last_login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Refresh from database
    user.refresh_from_db()

    # Deactivation status should be deleted
    assert not hasattr(user, "deactivation_status")
    assert not UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signal_deletes_deactivation_status_on_last_api_use_update():
    """
    Test signal deletes UserDeactivationStatus when last_api_use is updated.

    Verifies that updating last_api_use triggers signal to delete deactivation status.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")
    UserDeactivationStatus.objects.create(user=user)

    assert hasattr(user, "deactivation_status")

    # Update last_api_use
    user.last_api_use = timezone.now().date()
    user.save(update_fields=["last_api_use"])

    # Refresh from database
    user.refresh_from_db()

    # Deactivation status should be deleted
    assert not hasattr(user, "deactivation_status")
    assert not UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signal_deletes_deactivation_status_on_reactivated_at_update():
    """
    Test signal deletes UserDeactivationStatus when reactivated_at is updated.

    Verifies that updating reactivated_at triggers signal to delete deactivation status.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")
    UserDeactivationStatus.objects.create(user=user)

    assert hasattr(user, "deactivation_status")

    # Update reactivated_at (simulating admin reactivation)
    user.reactivated_at = timezone.now()
    user.save(update_fields=["reactivated_at"])

    # Refresh from database
    user.refresh_from_db()

    # Deactivation status should be deleted
    assert not hasattr(user, "deactivation_status")
    assert not UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signal_does_not_delete_on_other_field_updates():
    """
    Test signal does not delete UserDeactivationStatus when other fields are updated.

    Verifies that updating non-activity fields does not trigger deletion.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")
    UserDeactivationStatus.objects.create(user=user)

    assert hasattr(user, "deactivation_status")

    # Update a different field
    user.first_name = "John"
    user.save(update_fields=["first_name"])

    # Refresh from database
    user.refresh_from_db()

    # Deactivation status should still exist
    assert hasattr(user, "deactivation_status")
    assert UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_signal_handles_missing_deactivation_status():
    """
    Test signal handles case where UserDeactivationStatus does not exist.

    Verifies that signal does not error when no deactivation status exists.
    """
    user = User.objects.create_user(username="testuser", email="test@example.com")

    # No deactivation status created
    assert not hasattr(user, "deactivation_status")

    # Update last_login should not error
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Should complete without error
    user.refresh_from_db()
    assert user.last_login is not None


@pytest.mark.django_db
def test_signal_deletes_status_when_is_active_set_to_true():
    """Test that signal deletes deactivation status when admin sets is_active=True."""
    # Create a deactivated user with deactivation status
    user = User.objects.create_user(username="deactivated_user", email="deactivated@example.com")
    user.is_active = False
    user.save()

    UserDeactivationStatus.objects.create(
        user=user,
        one_month_email_sent_at=timezone.now() - timedelta(days=40),
        one_week_email_sent_at=timezone.now() - timedelta(days=17),
        one_day_email_sent_at=timezone.now() - timedelta(days=11),
        deactivated_at=timezone.now() - timedelta(days=10),
    )

    assert UserDeactivationStatus.objects.filter(user=user).exists()
    assert user.reactivated_at is None

    # Admin sets is_active=True in the detail page
    user.is_active = True
    user.save(update_fields=["is_active"])

    # Verify deactivation status was deleted
    assert not UserDeactivationStatus.objects.filter(user=user).exists()

    # Verify reactivated_at was automatically set
    user.refresh_from_db()
    assert user.reactivated_at is not None
