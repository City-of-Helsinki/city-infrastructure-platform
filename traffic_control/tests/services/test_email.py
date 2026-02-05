"""Tests for email service."""

import pytest
from django.core import mail
from django.test import override_settings

from traffic_control.services.email import send_email


@pytest.mark.django_db
def test_send_email_single_recipient() -> None:
    """Test sending email to a single valid recipient.

    Verifies that the email is successfully sent with correct content.
    """
    subject = "Test Subject"
    message = "Test message body"
    recipient = "test@example.com"

    result = send_email(
        subject=subject,
        message=message,
        recipient_list=[recipient],
    )

    assert result == 1
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.subject == subject
    assert email.body == message
    assert email.to == [recipient]


@pytest.mark.django_db
def test_send_email_multiple_recipients() -> None:
    """Test sending email to multiple valid recipients.

    Verifies that the email is sent to all recipients successfully.
    """
    subject = "Test Subject"
    message = "Test message body"
    recipients = ["test1@example.com", "test2@example.com", "test3@example.com"]

    result = send_email(
        subject=subject,
        message=message,
        recipient_list=recipients,
    )

    assert result == 1
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == recipients


@pytest.mark.django_db
def test_send_email_with_html_message() -> None:
    """Test sending email with HTML content.

    Verifies that HTML message is properly included in the email.
    """
    subject = "Test Subject"
    message = "Plain text message"
    html_message = "<p>HTML message</p>"
    recipient = "test@example.com"

    result = send_email(
        subject=subject,
        message=message,
        recipient_list=[recipient],
        html_message=html_message,
    )

    assert result == 1
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.body == message
    assert email.alternatives[0][0] == html_message
    assert email.alternatives[0][1] == "text/html"


@pytest.mark.parametrize(
    "from_email",
    [
        "cityinfra@hel.fi",
        "custom@example.com",
        "another@test.org",
    ],
)
@pytest.mark.django_db
def test_send_email_uses_default_from_email(from_email: str) -> None:
    """Test that send_email uses DEFAULT_FROM_EMAIL setting.

    Args:
        from_email: The email address to use as the sender.
    """
    with override_settings(DEFAULT_FROM_EMAIL=from_email):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=["test@example.com"],
        )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].from_email == from_email


@pytest.mark.django_db
def test_send_email_empty_recipient_list() -> None:
    """Test that empty recipient list raises ValueError.

    Verifies that the function validates recipient list is not empty.
    """
    with pytest.raises(ValueError, match="No recipient email addresses provided"):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=[],
        )


@pytest.mark.parametrize(
    "invalid_email",
    [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com",
        "injection\nBcc: attacker@evil.com",
        "injection\rBcc: attacker@evil.com",
        "multiple@@@signs@email.com",
        "",
    ],
)
@pytest.mark.django_db
def test_send_email_invalid_email_address(invalid_email: str) -> None:
    """Test that invalid email addresses raise ValueError.

    Verifies that the function validates email address format to prevent
    injection attacks and malformed addresses.

    Args:
        invalid_email: Invalid email address to test.
    """
    with pytest.raises(ValueError, match="Invalid email address"):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=[invalid_email],
        )


@pytest.mark.django_db
def test_send_email_invalid_email_sanitized_in_error() -> None:
    """Test that error message for invalid email is sanitized.

    Verifies that newlines and carriage returns are removed from
    error messages to prevent log injection.
    """
    invalid_email = "injection\nBcc: attacker@evil.com"

    with pytest.raises(ValueError) as exc_info:
        send_email(
            subject="Test",
            message="Test",
            recipient_list=[invalid_email],
        )

    error_message = str(exc_info.value)
    assert "\n" not in error_message
    assert "\r" not in error_message
    assert "Invalid email address" in error_message


@pytest.mark.django_db
def test_send_email_too_many_recipients() -> None:
    """Test that exceeding max recipients raises ValueError.

    Verifies that the function enforces maximum recipient limit
    to prevent abuse.
    """
    # Create 11 recipients (default max is 10)
    recipients = [f"test{i}@example.com" for i in range(11)]

    with pytest.raises(ValueError, match="Too many recipients. Maximum allowed: 10"):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=recipients,
        )


@pytest.mark.django_db
def test_send_email_custom_max_recipients() -> None:
    """Test that custom max_recipients parameter works correctly.

    Verifies that the max_recipients parameter can be customized.
    """
    # Create 5 recipients with custom max of 3
    recipients = [f"test{i}@example.com" for i in range(5)]

    with pytest.raises(ValueError, match="Too many recipients. Maximum allowed: 3"):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=recipients,
            max_recipients=3,
        )


@pytest.mark.django_db
def test_send_email_custom_max_recipients_allows_more() -> None:
    """Test that custom max_recipients allows more than default.

    Verifies that max_recipients can be increased beyond the default of 10.
    """
    # Create 15 recipients with custom max of 20
    recipients = [f"test{i}@example.com" for i in range(15)]

    result = send_email(
        subject="Test",
        message="Test",
        recipient_list=recipients,
        max_recipients=20,
    )

    assert result == 1
    assert len(mail.outbox) == 1
    assert len(mail.outbox[0].to) == 15


@pytest.mark.django_db
def test_send_email_exactly_max_recipients() -> None:
    """Test sending email with exactly max recipients allowed.

    Verifies that the function allows exactly the maximum number.
    """
    # Create exactly 10 recipients (default max)
    recipients = [f"test{i}@example.com" for i in range(10)]

    result = send_email(
        subject="Test",
        message="Test",
        recipient_list=recipients,
    )

    assert result == 1
    assert len(mail.outbox) == 1
    assert len(mail.outbox[0].to) == 10


@pytest.mark.django_db
def test_send_email_mixed_valid_and_invalid() -> None:
    """Test that one invalid email in list fails entire operation.

    Verifies that validation checks all recipients and fails if any are invalid.
    """
    recipients = [
        "valid1@example.com",
        "invalid-email",
        "valid2@example.com",
    ]

    with pytest.raises(ValueError, match="Invalid email address"):
        send_email(
            subject="Test",
            message="Test",
            recipient_list=recipients,
        )

    # Verify no email was sent
    assert len(mail.outbox) == 0
