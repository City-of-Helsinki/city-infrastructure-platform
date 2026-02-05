import pytest
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings


@pytest.mark.parametrize(
    "from_email",
    [
        "cityinfra@hel.fi",
        "custom@example.com",
        "another@test.org",
    ],
)
@pytest.mark.django_db
def test_send_test_email_single_recipient(from_email: str) -> None:
    """Test sending email to a single recipient.

    Verifies that the command successfully sends an email with correct
    sender, subject, and recipient information.

    Args:
        from_email: The email address to use as the sender.
    """

    recipient = "test@example.com"

    with override_settings(DEFAULT_FROM_EMAIL=from_email):
        call_command("send_test_email", "--recipient", recipient)

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.subject == "Cityinfra email test"
    assert email.body == "Test message"
    assert email.from_email == from_email
    assert email.to == [recipient]


@pytest.mark.parametrize(
    "from_email",
    [
        "cityinfra@hel.fi",
        "custom@example.com",
        "another@test.org",
    ],
)
@pytest.mark.django_db
def test_send_test_email_multiple_recipients(from_email: str) -> None:
    """Test sending email to multiple comma-separated recipients.

    Verifies that the command correctly parses comma-separated email
    addresses and sends to all recipients.
    """
    recipients = "test1@example.com,test2@example.com,test3@example.com"
    expected_recipients = ["test1@example.com", "test2@example.com", "test3@example.com"]

    with override_settings(DEFAULT_FROM_EMAIL=from_email):
        call_command("send_test_email", "--recipient", recipients)

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.subject == "Cityinfra email test"
    assert email.from_email == from_email
    assert email.to == expected_recipients


@pytest.mark.django_db
def test_send_test_email_with_whitespace() -> None:
    """Test sending email with whitespace around recipient addresses.

    Verifies that the command strips whitespace from recipient email addresses.
    """
    recipients = "test1@example.com , test2@example.com , test3@example.com"
    expected_recipients = ["test1@example.com", "test2@example.com", "test3@example.com"]

    call_command("send_test_email", "--recipient", recipients)

    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.to == expected_recipients


@pytest.mark.django_db
def test_send_test_email_missing_recipient() -> None:
    """Test command fails when recipient argument is missing.

    Verifies that the command raises an error when the required
    --recipient argument is not provided.
    """
    with pytest.raises(CommandError):
        call_command("send_test_email")


@pytest.mark.django_db
def test_send_test_email_invalid_email() -> None:
    """Test command fails with invalid email address.

    Verifies that the command validates email addresses and rejects
    invalid formats to prevent injection attacks.
    """
    invalid_emails = [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com",
        "injection\nBcc: attacker@evil.com",
    ]

    for invalid_email in invalid_emails:
        with pytest.raises(CommandError, match="Invalid email address"):
            call_command("send_test_email", "--recipient", invalid_email)


@pytest.mark.django_db
def test_send_test_email_too_many_recipients() -> None:
    """Test command fails when too many recipients are provided.

    Verifies that the command enforces a maximum number of recipients
    to prevent abuse.
    """
    # Create 11 recipients (max is 10)
    recipients = ",".join([f"test{i}@example.com" for i in range(11)])

    with pytest.raises(CommandError, match="Too many recipients"):
        call_command("send_test_email", "--recipient", recipients)


@pytest.mark.django_db
def test_send_test_email_empty_recipients() -> None:
    """Test command fails with empty recipient list.

    Verifies that the command rejects empty or whitespace-only recipient strings.
    """
    with pytest.raises(CommandError, match="No recipient email addresses provided"):
        call_command("send_test_email", "--recipient", "  ,  ,  ")
