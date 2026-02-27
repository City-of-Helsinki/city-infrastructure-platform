"""Django management command to notify inactive users and deactivate accounts after 6 months of inactivity.

Suggested cron schedule: Daily at 2 AM via cron: 0 2 * * *
"""

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.template.loader import render_to_string
from django.utils import timezone

from traffic_control.services.email import send_email
from users.models import User, UserDeactivationStatus
from users.utils import get_admin_notification_recipients


class Command(BaseCommand):
    """Notify inactive users and deactivate accounts after 6 months."""

    help = "Send notifications to inactive users and deactivate accounts after 180 days of inactivity"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Run without sending emails or updating database",
        )

    def handle(self, *args: Any, **options: dict) -> None:
        """
        Execute the command to notify inactive users and deactivate accounts.

        Args:
            *args: Positional arguments.
            **options: Command options including 'dry_run'.
        """
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No emails will be sent, no changes will be made"))

        now = timezone.now()
        processed_count = 0
        notified_count = 0
        deactivated_count = 0

        # Get all active users excluding AnonymousUser
        users = User.objects.filter(is_active=True).exclude(username="AnonymousUser")

        for user in users:
            # Process user and get action taken
            action_result = self._process_user(user, now, dry_run)
            if action_result == "deactivated":
                deactivated_count += 1
            elif action_result == "notified":
                notified_count += 1

            processed_count += 1
            # Log progress every 10 users
            if processed_count % 10 == 0:
                self.stdout.write(f"Processed {processed_count} users...")

        # Summary
        self._print_summary(dry_run, processed_count, notified_count, deactivated_count)

    def _process_user(self, user: User, now, dry_run: bool) -> str:
        """
        Process a single user and determine appropriate action.

        Args:
            user (User): The user to process.
            now: Current timestamp.
            dry_run (bool): If True, don't make actual changes.

        Returns:
            str: Action taken ('deactivated', 'notified', or 'skipped').
        """
        last_activity = self._get_last_activity(user)

        if last_activity is None:
            return "skipped"

        days_inactive = (now - last_activity).days

        return self._handle_inactivity_threshold(user, days_inactive, now, dry_run)

    def _get_last_activity(self, user: User):
        """
        Calculate the most recent activity timestamp for a user.

        Args:
            user (User): The user to check.

        Returns:
            datetime or None: Most recent activity timestamp or None if no activity.
        """
        activity_timestamps = []

        if user.last_login is not None:
            activity_timestamps.append(user.last_login)

        if user.last_api_use is not None:
            # Convert date to datetime at midnight
            activity_timestamps.append(
                timezone.make_aware(timezone.datetime.combine(user.last_api_use, timezone.datetime.min.time()))
            )

        if user.reactivated_at is not None:
            activity_timestamps.append(user.reactivated_at)

        if user.date_joined is not None:
            activity_timestamps.append(user.date_joined)

        if not activity_timestamps:
            return None

        return max(activity_timestamps)

    def _handle_inactivity_threshold(self, user: User, days_inactive: int, now, dry_run: bool) -> str:
        """
        Handle user based on inactivity threshold.

        Args:
            user (User): The user to process.
            days_inactive (int): Number of days user has been inactive.
            now: Current timestamp.
            dry_run (bool): If True, don't make actual changes.

        Returns:
            str: Action taken ('deactivated', 'notified', or 'skipped').
        """
        if days_inactive >= 180:
            return self._deactivate_user(user, days_inactive, now, dry_run)

        if days_inactive >= 179:
            return self._send_threshold_notification(user, days_inactive, now, dry_run, "one_day", 1)

        if days_inactive >= 173:
            return self._send_threshold_notification(user, days_inactive, now, dry_run, "one_week", 7)

        if days_inactive >= 150:
            return self._send_threshold_notification(user, days_inactive, now, dry_run, "one_month", 30)

        return "skipped"

    def _deactivate_user(self, user: User, days_inactive: int, now, dry_run: bool) -> str:
        """
        Deactivate a user account.

        Args:
            user (User): The user to deactivate.
            days_inactive (int): Number of days user has been inactive.
            now: Current timestamp.
            dry_run (bool): If True, don't make actual changes.

        Returns:
            str: 'deactivated'.
        """
        if not dry_run:
            user.is_active = False
            user.save(update_fields=["is_active"])

            status, created = UserDeactivationStatus.objects.get_or_create(user=user)
            status.deactivated_at = now
            status.save(update_fields=["deactivated_at"])

        self.stdout.write(
            self.style.ERROR(f"{'[DRY RUN] Would deactivate' if dry_run else 'Deactivated'} user: {user.username}")
        )

        # Send deactivation notice
        self._send_notification(
            user=user,
            template_name="deactivation_notice",
            days_until_deactivation=0,
            days_inactive=days_inactive,
            dry_run=dry_run,
        )

        return "deactivated"

    def _send_threshold_notification(
        self, user: User, days_inactive: int, now, dry_run: bool, threshold: str, days: int
    ) -> str:
        """
        Send notification for a specific threshold if needed.

        Args:
            user (User): The user to notify.
            days_inactive (int): Number of days user has been inactive.
            now: Current timestamp.
            dry_run (bool): If True, don't make actual changes.
            threshold (str): Threshold name ('one_day', 'one_week', 'one_month').
            days (int): Days until deactivation.

        Returns:
            str: 'notified' if email was sent, 'skipped' otherwise.
        """
        field_name = f"{threshold}_email_sent_at"

        if not self._should_send_notification(user, field_name):
            return "skipped"

        self._send_notification(
            user=user,
            template_name=f"inactive_warning_{threshold}",
            days_until_deactivation=days,
            days_inactive=days_inactive,
            dry_run=dry_run,
        )

        if not dry_run:
            status, created = UserDeactivationStatus.objects.get_or_create(user=user)
            setattr(status, field_name, now)
            status.save(update_fields=[field_name])

        return "notified"

    def _print_summary(self, dry_run: bool, processed: int, notified: int, deactivated: int) -> None:
        """
        Print summary of command execution.

        Args:
            dry_run (bool): Whether this was a dry run.
            processed (int): Total users processed.
            notified (int): Total notifications sent.
            deactivated (int): Total users deactivated.
        """
        self.stdout.write(self.style.SUCCESS(f"\n{'[DRY RUN] ' if dry_run else ''}Summary:"))
        self.stdout.write(f"Total users processed: {processed}")
        self.stdout.write(f"Notifications sent: {notified}")
        self.stdout.write(f"Users deactivated: {deactivated}")

    def _should_send_notification(self, user: User, field_name: str) -> bool:
        """
        Check if notification should be sent based on existing status.

        Args:
            user (User): The user to check.
            field_name (str): The timestamp field name to check.

        Returns:
            bool: True if notification should be sent, False otherwise.
        """
        if not hasattr(user, "deactivation_status"):
            return True

        status = user.deactivation_status
        timestamp = getattr(status, field_name, None)
        return timestamp is None

    def _render_email_templates(
        self, template_name: str, context: dict, user_has_email: bool
    ) -> tuple[str, str, str] | None:
        """
        Render email templates based on whether user has email.

        Args:
            template_name (str): Base name of the email template.
            context (dict): Template context.
            user_has_email (bool): Whether user has email (False = use admin notification template).

        Returns:
            tuple[str, str, str] | None: (subject, text_body, html_body) or None if rendering fails.
        """
        if user_has_email:
            # Use regular user notification templates
            subject_template = f"users/emails/{template_name}_subject.txt"
            text_template = f"users/emails/{template_name}.txt"
            html_template = f"users/emails/{template_name}.html"
        else:
            # Use admin notification templates for users without email
            subject_template = "users/emails/user_no_email_notification_subject.txt"
            text_template = "users/emails/user_no_email_notification.txt"
            html_template = "users/emails/user_no_email_notification.html"

        try:
            subject = render_to_string(subject_template, context).strip()
            text_body = render_to_string(text_template, context)
            html_body = render_to_string(html_template, context)
            return subject, text_body, html_body
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to render templates: {e}"))
            return None

    def _send_notification(
        self,
        user: User,
        template_name: str,
        days_until_deactivation: int,
        days_inactive: int,
        dry_run: bool,
    ) -> None:
        """
        Send notification email to user or admins if user has no email.

        Args:
            user (User): The user to notify.
            template_name (str): Base name of the email template.
            days_until_deactivation (int): Days remaining until deactivation.
            days_inactive (int): Number of days the user has been inactive.
            dry_run (bool): If True, don't actually send emails.
        """
        context = {
            "user": user,
            "days_until_deactivation": days_until_deactivation,
            "days_inactive": days_inactive,
            "deactivation_date": timezone.now() + timedelta(days=days_until_deactivation),
            "admin_emails": ", ".join(get_admin_notification_recipients()),
        }

        # Determine recipients
        if user.email:
            recipients = [user.email]
            recipient_type = "user"
            user_has_email = True
        else:
            # User has no email, notify admins
            recipients = get_admin_notification_recipients()
            if not recipients:
                self.stdout.write(
                    self.style.WARNING(
                        f"No admin notification recipients configured for user {user.username} without email. "
                        "Set 'Receives admin notification emails' flag on admin users."
                    )
                )
                return
            recipient_type = "admin"
            user_has_email = False

        # Render email templates
        templates = self._render_email_templates(template_name, context, user_has_email)
        if templates is None:
            # Error already logged in _render_email_templates
            return

        subject, text_body, html_body = templates

        if dry_run:
            # Make it clear what type of notification this is
            notification_type = (
                "DEACTIVATION" if days_until_deactivation == 0 else f"{days_until_deactivation}-DAY WARNING"
            )
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would send {notification_type} email '{template_name}' to {recipient_type}: "
                    f"{', '.join(recipients)} for user {user.username} (inactive {days_inactive} days)"
                )
            )
            return

        # Send email
        try:
            send_email(
                subject=subject,
                message=text_body,
                recipient_list=recipients,
                html_message=html_body,
                max_recipients=50,  # Increased for admin emails
            )
            notification_type = (
                "DEACTIVATION" if days_until_deactivation == 0 else f"{days_until_deactivation}-DAY WARNING"
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent {notification_type} email '{template_name}' to {recipient_type}: "
                    f"{', '.join(recipients)} for user {user.username} (inactive {days_inactive} days)"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email to {recipient_type} for {user.username}: {e}"))
