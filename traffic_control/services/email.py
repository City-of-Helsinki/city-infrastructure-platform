from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email


def send_email(
    subject: str,
    message: str,
    recipient_list: list[str],
    fail_silently: bool = False,
    html_message: str | None = None,
    max_recipients: int = 10,
) -> int:
    """
    Sends an email using Django's send_mail with from_email set to None.
    This will use the DEFAULT_FROM_EMAIL from Django settings.

    Security measures implemented:
    - Email addresses are validated using Django's validate_email()
    - Maximum recipients limit to prevent abuse
    - Django's send_mail() automatically sanitizes email headers

    Args:
        subject (str): The subject line of the email.
        message (str): The plain text message body.
        recipient_list (list[str]): List of recipient email addresses.
        fail_silently (bool): If True, exceptions during send are suppressed. Defaults to False.
        html_message (str | None): Optional HTML version of the message. Defaults to None.
        max_recipients (int): Maximum number of recipients allowed. Defaults to 10.

    Returns:
        int: Number of successfully sent emails.

    Raises:
        ValueError: If any email address is invalid, recipient list is empty, or too many recipients.
    """
    # Validate recipient list is not empty
    if not recipient_list:
        raise ValueError("No recipient email addresses provided")

    # Validate all recipient email addresses to prevent injection attacks
    # This prevents malformed addresses and email header injection attempts
    for recipient in recipient_list:
        try:
            validate_email(recipient)
        except ValidationError:
            # Sanitize error message to prevent log injection
            safe_recipient = recipient.replace("\n", "").replace("\r", "")[:100]
            raise ValueError(f"Invalid email address: {safe_recipient}")

    # Limit number of recipients to prevent abuse and spam
    if len(recipient_list) > max_recipients:
        raise ValueError(f"Too many recipients. Maximum allowed: {max_recipients}")

    return send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        html_message=html_message,
    )
