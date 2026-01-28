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

        Args:
            *args: Positional arguments.
            **options: Command options including 'recipient'.

        Raises:
            CommandError: If email sending fails due to SMTP or configuration errors.
        """
        recipient_input = options["recipient"]
        recipients = [email.strip() for email in recipient_input.split(",") if email.strip()]

        # Validate all recipient email addresses to prevent injection attacks
        for recipient in recipients:
            try:
                validate_email(recipient)
            except ValidationError:
                raise CommandError(f"Invalid email address: {recipient}")

        if not recipients:
            raise CommandError("No valid recipient email addresses provided")

        # Limit number of recipients to prevent abuse
        max_recipients = 10
        if len(recipients) > max_recipients:
            raise CommandError(f"Too many recipients. Maximum allowed: {max_recipients}")

        sender = "cityinfra@hel.fi"
        subject = "Cityinfra email test"
        message = "Test message"

        self.stdout.write(f"Sending test email to: {', '.join(recipients)}")
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
