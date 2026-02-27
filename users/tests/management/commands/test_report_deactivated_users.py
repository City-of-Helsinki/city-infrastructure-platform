"""Tests for report_deactivated_users management command."""

from calendar import month_name
from datetime import timedelta
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from users.models import User, UserDeactivationStatus


@pytest.fixture
def deactivated_user_in_month(db):
    """Create a deactivated user in a specific month."""

    def _create(username, email, month_offset=0):
        """
        Create deactivated user.

        Args:
            username: Username for the user.
            email: Email for the user.
            month_offset: 0 = current month, -1 = last month, -2 = 2 months ago, etc.
        """
        user = User.objects.create_user(username=username, email=email, is_active=False)

        # Calculate target date in the specified month
        now = timezone.now()
        target_month = now.month + month_offset
        target_year = now.year

        # Handle year boundaries
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1

        deactivation_date = now.replace(
            year=target_year,
            month=target_month,
            day=15,  # Middle of month
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )

        status = UserDeactivationStatus.objects.create(user=user, deactivated_at=deactivation_date)

        return user, status

    return _create


@pytest.fixture
def admin_notification_recipient(db):
    """Create a user who receives admin notifications."""

    def _create(username="admin", email="admin@example.com"):
        return User.objects.create_user(
            username=username, email=email, receives_admin_notification_emails=True, is_active=True
        )

    return _create


@pytest.mark.django_db
def test_report_previous_month_deactivations(deactivated_user_in_month, admin_notification_recipient):
    """Test report includes users deactivated in previous month."""
    admin_notification_recipient()

    # Create user deactivated last month
    user, status = deactivated_user_in_month("lastmonth", "last@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    # Email should be sent
    assert len(mail.outbox) == 1
    assert "admin@example.com" in mail.outbox[0].to

    # Email should contain user details
    email_body = mail.outbox[0].body
    assert user.username in email_body
    assert user.email in email_body


@pytest.mark.django_db
def test_report_dry_run_mode(deactivated_user_in_month, admin_notification_recipient):
    """Test dry-run mode doesn't send emails."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    out = StringIO()
    call_command("report_deactivated_users", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "DRY RUN MODE" in output
    assert "Would send monthly report" in output

    # No email should be sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_empty_report_no_deactivations(db, admin_notification_recipient):
    """Test report handles no deactivations gracefully."""
    admin_notification_recipient()

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    assert "Found 0 deactivated users" in output
    assert "No deactivated users to report" in output

    # No email should be sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_exclude_current_month_deactivations(deactivated_user_in_month, admin_notification_recipient):
    """Test current month deactivations are excluded from report."""
    admin_notification_recipient()

    # Create user deactivated this month
    deactivated_user_in_month("thismonth", "this@example.com", month_offset=0)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    # Should find 0 users (current month excluded)
    assert "Found 0 deactivated users" in output
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_exclude_older_month_deactivations(deactivated_user_in_month, admin_notification_recipient):
    """Test deactivations from 2+ months ago are excluded."""
    admin_notification_recipient()

    # Create user deactivated 2 months ago
    deactivated_user_in_month("twomonthsago", "two@example.com", month_offset=-2)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    # Should find 0 users (too old)
    assert "Found 0 deactivated users" in output
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_send_to_multiple_admins(deactivated_user_in_month, admin_notification_recipient):
    """Test report is sent to all configured admin emails."""
    # Create two admins who receive notifications
    admin_notification_recipient("admin1", "admin1@example.com")
    admin_notification_recipient("admin2", "admin2@example.com")

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    assert "admin1@example.com" in mail.outbox[0].to
    assert "admin2@example.com" in mail.outbox[0].to


@pytest.mark.django_db
def test_error_when_no_admins_configured(deactivated_user_in_month):
    """Test command shows error when no admin notification recipients configured."""
    # Don't create any admin recipients
    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    assert "No admin notification recipients configured" in output


@pytest.mark.django_db
def test_report_contains_month_and_year(deactivated_user_in_month, admin_notification_recipient):
    """Test report includes correct month name and year."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    # Calculate previous month
    now = timezone.now()
    last_month = now.replace(day=1) - timedelta(days=1)
    expected_month = month_name[last_month.month]
    expected_year = str(last_month.year)

    output = out.getvalue()
    assert expected_month in output
    assert expected_year in output


@pytest.mark.django_db
def test_report_email_contains_table(deactivated_user_in_month, admin_notification_recipient):
    """Test report email contains user details in table format."""
    admin_notification_recipient()

    user1, _ = deactivated_user_in_month("user1", "user1@example.com", month_offset=-1)
    user2, _ = deactivated_user_in_month("user2", "user2@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body

    # Should contain both usernames
    assert user1.username in email_body
    assert user2.username in email_body

    # Should contain both emails
    assert user1.email in email_body
    assert user2.email in email_body


@pytest.mark.django_db
def test_report_email_subject_in_english(deactivated_user_in_month, admin_notification_recipient):
    """Test report email subject is in English."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    subject = mail.outbox[0].subject
    # Should be in English
    assert "Monthly" in subject or "Report" in subject or "Deactivated" in subject


@pytest.mark.django_db
def test_report_user_count_in_output(deactivated_user_in_month, admin_notification_recipient):
    """Test report shows correct count of deactivated users."""
    admin_notification_recipient()

    # Create 3 deactivated users
    for i in range(3):
        deactivated_user_in_month(f"user{i}", f"user{i}@example.com", month_offset=-1)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    assert "Found 3 deactivated users" in output
    assert "Report included 3 deactivated users" in output


@pytest.mark.django_db
def test_report_only_includes_users_with_deactivated_at(db, admin_notification_recipient):
    """Test report only includes users with deactivated_at timestamp."""
    admin_notification_recipient()

    # Create user with status but no deactivated_at
    user = User.objects.create_user(username="pending", email="pending@example.com")
    UserDeactivationStatus.objects.create(
        user=user,
        one_month_email_sent_at=timezone.now() - timedelta(days=40),
        # No deactivated_at set
    )

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    # Should find 0 users (no deactivated_at)
    output = out.getvalue()
    assert "Found 0 deactivated users" in output


@pytest.mark.django_db
def test_report_html_and_text_versions(deactivated_user_in_month, admin_notification_recipient):
    """Test report email has both HTML and text versions."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Should have both body (text) and alternatives (HTML)
    assert email.body  # Text version
    assert len(email.alternatives) > 0  # HTML version
    assert email.alternatives[0][1] == "text/html"


@pytest.mark.django_db
def test_report_trilingual_content(deactivated_user_in_month, admin_notification_recipient):
    """Test report contains Finnish, Swedish, and English text."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body

    # Should contain text in all three languages
    # Finnish indicators
    assert any(word in email_body for word in ["Poistettu", "käyttäjä", "KUUKAUSIRAPORTTI"])
    # Swedish indicators
    assert any(word in email_body for word in ["Inaktiverad", "användare", "MÅNADSRAPPORT"])
    # English indicators
    assert any(word in email_body for word in ["Deactivated", "user", "REPORT"])


@pytest.mark.django_db
def test_report_success_message(deactivated_user_in_month, admin_notification_recipient):
    """Test command outputs success message after sending report."""
    admin_notification_recipient()

    deactivated_user_in_month("test", "test@example.com", month_offset=-1)

    out = StringIO()
    call_command("report_deactivated_users", stdout=out)

    output = out.getvalue()
    assert "Successfully sent monthly deactivation report" in output
    assert "admin@example.com" in output


@pytest.mark.django_db
def test_report_orders_by_deactivation_date(deactivated_user_in_month, admin_notification_recipient):
    """Test report orders users by deactivation date."""
    admin_notification_recipient()

    now = timezone.now()

    # Create users deactivated on different days last month
    user1 = User.objects.create_user(username="user1", email="user1@example.com", is_active=False)
    user2 = User.objects.create_user(username="user2", email="user2@example.com", is_active=False)

    last_month = now.replace(day=1) - timedelta(days=1)

    UserDeactivationStatus.objects.create(user=user1, deactivated_at=last_month.replace(day=20))
    UserDeactivationStatus.objects.create(user=user2, deactivated_at=last_month.replace(day=10))

    call_command("report_deactivated_users")

    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body

    # user2 should appear before user1 (earlier date)
    user2_pos = email_body.find("user2")
    user1_pos = email_body.find("user1")
    assert user2_pos < user1_pos


@pytest.mark.django_db
def test_report_custom_month_parameter(deactivated_user_in_month, admin_notification_recipient):
    """Test report with custom --month parameter."""
    admin_notification_recipient()

    now = timezone.now()

    # Create user deactivated 2 months ago
    user, status = deactivated_user_in_month("user_two_months", "two@example.com", month_offset=-2)

    # Report for 2 months ago (custom month)
    two_months_ago = now.replace(day=1) - timedelta(days=35)
    target_month = two_months_ago.month
    target_year = two_months_ago.year

    out = StringIO()
    call_command("report_deactivated_users", month=target_month, year=target_year, stdout=out)

    output = out.getvalue()
    assert "custom month specified" in output
    assert "Found 1 deactivated users" in output

    # Email should be sent
    assert len(mail.outbox) == 1
    assert user.username in mail.outbox[0].body


@pytest.mark.django_db
def test_report_custom_month_uses_current_year_if_not_specified(
    deactivated_user_in_month, admin_notification_recipient
):
    """Test that custom --month uses current year if --year not specified."""
    admin_notification_recipient()

    now = timezone.now()

    # Create user deactivated in January of current year
    user = User.objects.create_user(username="jan_user", email="jan@example.com", is_active=False)
    jan_date = now.replace(month=1, day=15, hour=10, minute=0, second=0, microsecond=0)

    UserDeactivationStatus.objects.create(user=user, deactivated_at=jan_date)

    out = StringIO()
    call_command("report_deactivated_users", month=1, stdout=out)  # No --year specified

    output = out.getvalue()
    assert f"Generating report for January {now.year}" in output
    assert "Found 1 deactivated users" in output


@pytest.mark.django_db
def test_report_invalid_month_parameter(admin_notification_recipient):
    """Test that invalid --month parameter shows error."""
    admin_notification_recipient()

    out = StringIO()
    call_command("report_deactivated_users", month=13, stdout=out)  # Invalid month

    output = out.getvalue()
    assert "Invalid month: 13" in output
    assert "Must be between 1 and 12" in output

    # No email should be sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_report_invalid_month_zero(admin_notification_recipient):
    """Test that month=0 shows error."""
    admin_notification_recipient()

    out = StringIO()
    call_command("report_deactivated_users", month=0, stdout=out)

    output = out.getvalue()
    assert "Invalid month: 0" in output

    # No email should be sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_report_custom_month_and_year(deactivated_user_in_month, admin_notification_recipient):
    """Test report with both --month and --year parameters."""
    admin_notification_recipient()

    # Create user deactivated in December 2025
    user = User.objects.create_user(username="dec_2025_user", email="dec2025@example.com", is_active=False)
    dec_2025_date = timezone.datetime(2025, 12, 20, 10, 0, 0, 0)
    dec_2025_date = timezone.make_aware(dec_2025_date)

    UserDeactivationStatus.objects.create(user=user, deactivated_at=dec_2025_date)

    out = StringIO()
    call_command("report_deactivated_users", month=12, year=2025, stdout=out)

    output = out.getvalue()
    assert "Generating report for December 2025" in output
    assert "custom month specified" in output
    assert "Found 1 deactivated users" in output

    # Email should be sent
    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body
    assert user.username in email_body
    # Month and year should be in the email body
    assert "December" in email_body
    assert "2025" in email_body


@pytest.mark.django_db
def test_report_custom_month_no_users(admin_notification_recipient):
    """Test report for custom month with no deactivated users."""
    admin_notification_recipient()

    out = StringIO()
    # Report for January 2020 (no users deactivated then)
    call_command("report_deactivated_users", month=1, year=2020, stdout=out)

    output = out.getvalue()
    assert "Found 0 deactivated users in January 2020" in output
    assert "No deactivated users to report" in output

    # No email should be sent
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_report_custom_month_december_handles_year_boundary(admin_notification_recipient):
    """Test that December custom month correctly handles year boundary."""
    admin_notification_recipient()

    # Create user deactivated in December 2025
    user = User.objects.create_user(username="dec_user", email="dec@example.com", is_active=False)
    dec_date = timezone.datetime(2025, 12, 31, 23, 59, 0, 0)
    dec_date = timezone.make_aware(dec_date)

    UserDeactivationStatus.objects.create(user=user, deactivated_at=dec_date)

    # Should not include users from January 2026
    jan_user = User.objects.create_user(username="jan_user", email="jan@example.com", is_active=False)
    jan_date = timezone.datetime(2026, 1, 1, 0, 0, 0, 0)
    jan_date = timezone.make_aware(jan_date)

    UserDeactivationStatus.objects.create(user=jan_user, deactivated_at=jan_date)

    out = StringIO()
    call_command("report_deactivated_users", month=12, year=2025, stdout=out)

    output = out.getvalue()
    assert "Found 1 deactivated users in December 2025" in output

    # Email should only contain December user
    assert len(mail.outbox) == 1
    email_body = mail.outbox[0].body
    assert user.username in email_body
    assert jan_user.username not in email_body


@pytest.mark.django_db
def test_report_dry_run_with_custom_month(admin_notification_recipient):
    """Test dry-run mode with custom month parameter."""
    admin_notification_recipient()

    # Create user deactivated in a specific month
    user = User.objects.create_user(username="test_user", email="test@example.com", is_active=False)
    test_date = timezone.datetime(2025, 6, 15, 10, 0, 0, 0)
    test_date = timezone.make_aware(test_date)

    UserDeactivationStatus.objects.create(user=user, deactivated_at=test_date)

    out = StringIO()
    call_command("report_deactivated_users", "--dry-run", month=6, year=2025, stdout=out)

    output = out.getvalue()
    assert "DRY RUN MODE" in output
    assert "Generating report for June 2025" in output
    assert "Would send monthly report" in output

    # No email should be sent in dry-run
    assert len(mail.outbox) == 0
