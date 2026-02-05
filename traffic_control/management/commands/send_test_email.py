"""Django management command to send test emails."""

import smtplib
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from traffic_control.services.email import send_email


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
        - Email validation is handled by the send_email service function
        - Email body, subject, and sender are hardcoded (no user input)
        - Log output is sanitized to prevent log injection

        Args:
            *args: Positional arguments.
            **options: Command options including 'recipient'.

        Raises:
            CommandError: If email sending fails due to SMTP, configuration, or validation errors.
        """
        recipient_input = options["recipient"]
        recipients = [email.strip() for email in recipient_input.split(",") if email.strip()]

        # Security: All email content is hardcoded - no user input in email body, subject, or sender
        # This prevents email content injection attacks
        subject = "Cityinfra email test"
        message = "Test message"

        # Sanitize recipient list for logging to prevent log injection (remove newlines/carriage returns)
        safe_recipients_for_log = [r.replace("\n", "").replace("\r", "")[:100] for r in recipients]
        self.stdout.write(f"Sending test email to: {', '.join(safe_recipients_for_log)}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Subject: {subject}")

        try:
            send_email(
                subject=subject,
                message=message,
                recipient_list=recipients,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully sent test email to {len(recipients)} recipient(s)"))
        except ValueError as e:
            # Validation errors from send_email service
            raise CommandError(str(e))
        except smtplib.SMTPException as e:
            raise CommandError(f"SMTP error occurred. Please check your email server configuration. Error: {str(e)}")
        except Exception as e:
            raise CommandError(f"Failed to send email. Error: {str(e)}")
