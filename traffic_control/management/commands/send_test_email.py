"""Django management command to send test emails."""

import smtplib
from typing import Any

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.validators import validate_email


class Command(BaseCommand):
    """Django management command to send test emails for email configuration verification."""

    help = "Send a test email to verify email configuration"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "--recipient",
            type=str,
            required=True,
            help="Email recipient address(es), comma-separated for multiple recipients",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command to send test email.

        Security measures implemented:
        - Email addresses are validated using Django's validate_email()
        - Maximum 10 recipients to prevent abuse
        - Email body, subject, and sender are hardcoded (no user input)
        - Log output is sanitized to prevent log injection
        - Django's send_mail() automatically sanitizes email headers

        Args:
            *args: Positional arguments.
            **options: Command options including 'recipient'.

        Raises:
            CommandError: If email sending fails due to SMTP or configuration errors.
        """
        recipient_input = options["recipient"]
        recipients = [email.strip() for email in recipient_input.split(",") if email.strip()]

        # Security: Validate all recipient email addresses to prevent injection attacks
        # This prevents malformed addresses and email header injection attempts
        for recipient in recipients:
            try:
                validate_email(recipient)
            except ValidationError:
                # Sanitize error message to prevent log injection
                safe_recipient = recipient.replace("\n", "").replace("\r", "")[:100]
                raise CommandError(f"Invalid email address: {safe_recipient}")

        if not recipients:
            raise CommandError("No valid recipient email addresses provided")

        # Security: Limit number of recipients to prevent abuse and spam
        max_recipients = 10
        if len(recipients) > max_recipients:
            raise CommandError(f"Too many recipients. Maximum allowed: {max_recipients}")

        # Security: All email content is hardcoded - no user input in email body, subject, or sender
        # This prevents email content injection attacks
        sender = "cityinfra@hel.fi"
        subject = "Cityinfra email test"
        message = "Test message"

        # Note: recipients are already validated above, but we sanitize for logging
        # to prevent log injection (remove newlines/carriage returns)
        safe_recipients_for_log = [r.replace("\n", "").replace("\r", "") for r in recipients]
        self.stdout.write(f"Sending test email to: {', '.join(safe_recipients_for_log)}")
        self.stdout.write(f"From: {sender}")
        self.stdout.write(f"Subject: {subject}")

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=sender,
                recipient_list=recipients,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully sent test email to {len(recipients)} recipient(s)"))
        except smtplib.SMTPException as e:
            raise CommandError(f"SMTP error occurred. Please check your email server configuration. Error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Failed to send email. Error: {str(e)}")
