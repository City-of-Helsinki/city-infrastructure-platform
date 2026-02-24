"""Tests for notify_inactive_users management command."""

from datetime import timedelta
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from users.models import User, UserDeactivationStatus


@pytest.fixture
def create_user_with_activity(db):
    """Factory fixture to create users with specific activity dates."""

    def _create(username, email, days_ago_login=None, days_ago_api=None, days_ago_reactivated=None):
        user = User.objects.create_user(username=username, email=email)
        now = timezone.now()

        if days_ago_login is not None:
            user.last_login = now - timedelta(days=days_ago_login)

        if days_ago_api is not None:
            user.last_api_use = (now - timedelta(days=days_ago_api)).date()

        if days_ago_reactivated is not None:
            user.reactivated_at = now - timedelta(days=days_ago_reactivated)

        user.save()
        return user

    return _create


@pytest.mark.django_db
def test_notify_inactive_users_dry_run_mode(create_user_with_activity):
    """Test command runs in dry-run mode without making changes."""
    # Create user who should be deactivated (180+ days inactive)
    user = create_user_with_activity("testuser", "test@example.com", days_ago_login=185)

    out = StringIO()
    call_command("notify_inactive_users", "--dry-run", stdout=out)

    output = out.getvalue()

    # Check output mentions dry run
    assert "DRY RUN MODE" in output
    assert "Would deactivate" in output

    # Verify user was NOT actually deactivated
    user.refresh_from_db()
    assert user.is_active is True

    # Verify no UserDeactivationStatus was created
    assert not UserDeactivationStatus.objects.filter(user=user).exists()

    # Verify no emails were sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_deactivate_user_180_days_inactive(create_user_with_activity):
    """Test user is deactivated after 180 days of inactivity."""
    user = create_user_with_activity("inactive_user", "inactive@example.com", days_ago_login=181)

    call_command("notify_inactive_users")

    # Verify user was deactivated
    user.refresh_from_db()
    assert user.is_active is False

    # Verify UserDeactivationStatus was created with deactivated_at timestamp
    status = UserDeactivationStatus.objects.get(user=user)
    assert status.deactivated_at is not None

    # Verify deactivation email was sent
    assert len(mail.outbox) == 1
    assert "deactivated" in mail.outbox[0].subject.lower() or "Account Deactivated" in mail.outbox[0].subject


@pytest.mark.django_db
def test_send_one_month_warning_150_days_inactive(create_user_with_activity):
    """Test 30-day warning email is sent at 150 days inactive."""
    user = create_user_with_activity("user_150", "user150@example.com", days_ago_login=150)

    call_command("notify_inactive_users")

    # Verify user is still active
    user.refresh_from_db()
    assert user.is_active is True

    # Verify status was created with one_month_email_sent_at
    status = UserDeactivationStatus.objects.get(user=user)
    assert status.one_month_email_sent_at is not None
    assert status.deactivated_at is None

    # Verify email was sent
    assert len(mail.outbox) == 1
    assert "30" in mail.outbox[0].subject or "month" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_send_one_week_warning_173_days_inactive(create_user_with_activity):
    """Test 7-day warning email is sent at 173 days inactive."""
    user = create_user_with_activity("user_173", "user173@example.com", days_ago_login=173)

    call_command("notify_inactive_users")

    # Verify user is still active
    user.refresh_from_db()
    assert user.is_active is True

    # Verify status was created with one_week_email_sent_at
    status = UserDeactivationStatus.objects.get(user=user)
    assert status.one_week_email_sent_at is not None
    assert status.deactivated_at is None

    # Verify email was sent
    assert len(mail.outbox) == 1
    assert "7" in mail.outbox[0].subject or "week" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_send_one_day_warning_179_days_inactive(create_user_with_activity):
    """Test 1-day warning email is sent at 179 days inactive."""
    user = create_user_with_activity("user_179", "user179@example.com", days_ago_login=179)

    call_command("notify_inactive_users")

    # Verify user is still active
    user.refresh_from_db()
    assert user.is_active is True

    # Verify status was created with one_day_email_sent_at
    status = UserDeactivationStatus.objects.get(user=user)
    assert status.one_day_email_sent_at is not None
    assert status.deactivated_at is None

    # Verify email was sent
    assert len(mail.outbox) == 1
    assert "1" in mail.outbox[0].subject or "day" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_skip_user_with_recent_reactivation(create_user_with_activity):
    """Test user with recent reactivation is not deactivated."""
    # User was reactivated 50 days ago (most recent activity)
    user = create_user_with_activity(
        "reactivated_user",
        "reactivated@example.com",
        days_ago_login=200,  # Very old login
        days_ago_reactivated=50,  # Recent reactivation
    )

    call_command("notify_inactive_users")

    # Verify user is still active (only 50 days since reactivation)
    user.refresh_from_db()
    assert user.is_active is True

    # Verify no deactivation status created
    assert not UserDeactivationStatus.objects.filter(user=user).exists()

    # Verify no emails sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_use_most_recent_activity_timestamp(create_user_with_activity):
    """Test command uses the most recent of last_login, last_api_use, reactivated_at."""
    # User has old login but recent API use
    user = create_user_with_activity(
        "api_user",
        "api@example.com",
        days_ago_login=200,
        days_ago_api=50,  # Most recent
    )

    call_command("notify_inactive_users")

    # Should not be deactivated (only 50 days since API use)
    user.refresh_from_db()
    assert user.is_active is True
    assert not UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_skip_anonymous_user(db):
    """Test AnonymousUser is excluded from processing."""
    User.objects.get_or_create(username="AnonymousUser", defaults={"email": "anon@example.com"})

    out = StringIO()
    call_command("notify_inactive_users", stdout=out)

    # AnonymousUser should not appear in output
    output = out.getvalue()
    assert "AnonymousUser" not in output


@pytest.mark.django_db
def test_skip_user_with_no_activity_timestamps(db):
    """Test users with no activity timestamps are skipped."""
    user = User.objects.create_user(username="noactivity", email="noactivity@example.com")
    # Don't set any activity timestamps

    call_command("notify_inactive_users")

    # User should be unchanged
    user.refresh_from_db()
    assert user.is_active is True
    assert not UserDeactivationStatus.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_idempotency_do_not_resend_emails(create_user_with_activity):
    """Test emails are not resent if already sent."""
    create_user_with_activity("user_150", "user150@example.com", days_ago_login=150)

    # Run command first time
    call_command("notify_inactive_users")
    assert len(mail.outbox) == 1

    # Clear outbox and run again
    mail.outbox = []
    call_command("notify_inactive_users")

    # Email should NOT be sent again (timestamp already set)
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_user_without_email_notifies_admins(create_user_with_activity, settings):
    """Test users without email trigger admin notifications."""
    settings.DEACTIVATION_ADMIN_EMAILS = ["admin@example.com"]

    user = create_user_with_activity("noemail", "", days_ago_login=150)

    call_command("notify_inactive_users")

    # Email should be sent to admin, not user
    assert len(mail.outbox) == 1
    assert "admin@example.com" in mail.outbox[0].to
    assert user.username in mail.outbox[0].body


@pytest.mark.django_db
def test_progress_logging_every_10_users(create_user_with_activity):
    """Test progress is logged every 10 users."""
    # Create 15 users
    for i in range(15):
        create_user_with_activity(f"user{i}", f"user{i}@example.com", days_ago_login=50)

    out = StringIO()
    call_command("notify_inactive_users", stdout=out)

    output = out.getvalue()
    assert "Processed 10 users" in output


@pytest.mark.django_db
def test_summary_output(create_user_with_activity):
    """Test command outputs summary statistics."""
    create_user_with_activity("user1", "user1@example.com", days_ago_login=181)  # Deactivate
    create_user_with_activity("user2", "user2@example.com", days_ago_login=150)  # Notify
    create_user_with_activity("user3", "user3@example.com", days_ago_login=50)  # Skip

    out = StringIO()
    call_command("notify_inactive_users", stdout=out)

    output = out.getvalue()
    assert "Summary:" in output
    assert "Total users processed:" in output
    assert "Notifications sent:" in output
    assert "Users deactivated:" in output


@pytest.mark.django_db
def test_email_subject_in_english(create_user_with_activity):
    """Test email subjects are in English as specified."""
    create_user_with_activity("testuser", "test@example.com", days_ago_login=150)

    call_command("notify_inactive_users")

    assert len(mail.outbox) == 1
    # Subject should be in English (not Finnish or Swedish)
    subject = mail.outbox[0].subject
    # Check it's one of our English subjects
    assert any(keyword in subject for keyword in ["Account", "Inactivity", "Warning", "Deactivation"])


@pytest.mark.django_db
def test_multiple_thresholds_in_sequence(create_user_with_activity):
    """Test user progresses through thresholds correctly over time."""
    user = create_user_with_activity("progressive", "prog@example.com", days_ago_login=150)

    # First run: 150 days - should send 30-day warning
    call_command("notify_inactive_users")
    status = UserDeactivationStatus.objects.get(user=user)
    assert status.one_month_email_sent_at is not None
    assert status.one_week_email_sent_at is None

    # Simulate time passing to 173 days
    user.last_login = timezone.now() - timedelta(days=173)
    user.save()

    # Second run: 173 days - should send 7-day warning
    call_command("notify_inactive_users")
    status.refresh_from_db()
    assert status.one_week_email_sent_at is not None
    assert status.one_day_email_sent_at is None

    # Simulate time passing to 179 days
    user.last_login = timezone.now() - timedelta(days=179)
    user.save()

    # Third run: 179 days - should send 1-day warning
    call_command("notify_inactive_users")
    status.refresh_from_db()
    assert status.one_day_email_sent_at is not None

    # Simulate time passing to 181 days
    user.last_login = timezone.now() - timedelta(days=181)
    user.save()

    # Fourth run: 181 days - should deactivate
    call_command("notify_inactive_users")
    user.refresh_from_db()
    status.refresh_from_db()
    assert user.is_active is False
    assert status.deactivated_at is not None
