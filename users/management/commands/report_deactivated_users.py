"""Django management command to report deactivated users from the previous month to admins.
Suggested cron schedule: 1st of month at 3 AM via cron: 0 3 1 * *
"""
from calendar import month_name
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.template.loader import render_to_string
from django.utils import timezone

from traffic_control.services.email import send_email
from users.models import UserDeactivationStatus
from users.utils import get_admin_notification_recipients


class Command(BaseCommand):
    """Send monthly reports of deactivated users to administrators."""

    help = "Send monthly report of deactivated users from the previous month to admin emails"

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
            help="Run without sending emails",
        )
        parser.add_argument(
            "--month",
            type=int,
            dest="month",
            help="Month to report (1-12). If not specified, reports previous month.",
        )
        parser.add_argument(
            "--year",
            type=int,
            dest="year",
            help=(
                "Year to report (e.g., 2026). If not specified, uses current year "
                "or previous year if month is December."
            ),
        )

    def _calculate_custom_month_boundaries(self, custom_month: int, custom_year: int, now):
        """
        Calculate month boundaries for custom month/year.

        Args:
            custom_month (int): Target month (1-12).
            custom_year (int): Target year.
            now: Current timestamp.

        Returns:
            tuple: (first_day_report_month, first_day_after_report_month, target_month, target_year)
        """
        target_year = custom_year if custom_year is not None else now.year
        target_month = custom_month

        # Create first day of target month
        first_day_target_month = timezone.datetime(
            year=target_year, month=target_month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        first_day_target_month = timezone.make_aware(first_day_target_month)

        # Calculate first day of next month
        if target_month == 12:
            next_month = 1
            next_year = target_year + 1
        else:
            next_month = target_month + 1
            next_year = target_year

        first_day_next_month = timezone.datetime(
            year=next_year, month=next_month, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        first_day_next_month = timezone.make_aware(first_day_next_month)

        return first_day_target_month, first_day_next_month, target_month, target_year

    def _calculate_previous_month_boundaries(self, now):
        """
        Calculate month boundaries for previous month (default behavior).

        Args:
            now: Current timestamp.

        Returns:
            tuple: (first_day_report_month, first_day_after_report_month)
        """
        current_month_first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_previous_month = current_month_first - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return first_day_previous_month, current_month_first

    def handle(self, *args: Any, **options: dict) -> None:
        """
        Execute the command to send monthly deactivation report.

        Args:
            *args: Positional arguments.
            **options: Command options including 'dry_run', 'month', and 'year'.
        """
        dry_run = options["dry_run"]
        custom_month = options.get("month")
        custom_year = options.get("year")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No emails will be sent"))

        # Validate month parameter
        if custom_month is not None:
            if custom_month < 1 or custom_month > 12:
                self.stdout.write(self.style.ERROR(f"Invalid month: {custom_month}. Must be between 1 and 12."))
                return

        # Calculate month boundaries
        now = timezone.now()

        if custom_month is not None:
            # Use specified month
            (
                first_day_report_month,
                first_day_after_report_month,
                target_month,
                target_year,
            ) = self._calculate_custom_month_boundaries(custom_month, custom_year, now)

            self.stdout.write(
                f"Generating report for {month_name[target_month]} {target_year} (custom month specified)"
            )
        else:
            # Use previous month (default behavior)
            first_day_report_month, first_day_after_report_month = self._calculate_previous_month_boundaries(now)

        # Query deactivated users from target month
        deactivated_users = (
            UserDeactivationStatus.objects.filter(
                deactivated_at__gte=first_day_report_month,
                deactivated_at__lt=first_day_after_report_month,
                deactivated_at__isnull=False,
            )
            .select_related("user")
            .order_by("deactivated_at")
        )

        user_count = deactivated_users.count()
        self.stdout.write(
            f"Found {user_count} deactivated users in {month_name[first_day_report_month.month]} "
            f"{first_day_report_month.year}"
        )

        if user_count == 0:
            self.stdout.write(self.style.SUCCESS("No deactivated users to report."))
            return

        # Prepare context for email
        context = {
            "deactivated_users": deactivated_users,
            "month_name": month_name[first_day_report_month.month],
            "year": first_day_report_month.year,
            "user_count": user_count,
        }
        # Render email templates
        subject_template = "users/emails/admin_monthly_report_subject.txt"
        text_template = "users/emails/admin_monthly_report.txt"
        html_template = "users/emails/admin_monthly_report.html"
        try:
            subject = render_to_string(subject_template, context).strip()
            text_body = render_to_string(text_template, context)
            html_body = render_to_string(html_template, context)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to render email templates: {e}"))
            return

        # Get admin email recipients from database
        recipients = get_admin_notification_recipients()
        if not recipients:
            self.stdout.write(
                self.style.ERROR(
                    "No admin notification recipients configured. "
                    "Set 'Receives admin notification emails' flag on admin users."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would send monthly report to {len(recipients)} admin(s): " f"{', '.join(recipients)}"
                )
            )
            self.stdout.write(f"[DRY RUN] Report would include {user_count} deactivated users")
            return
        # Send email to admins
        try:
            send_email(
                subject=subject,
                message=text_body,
                recipient_list=recipients,
                html_message=html_body,
                max_recipients=100,  # Allow more recipients for admin distribution lists
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully sent monthly deactivation report to {len(recipients)} admin(s): "
                    f"{', '.join(recipients)}"
                )
            )
            self.stdout.write(f"Report included {user_count} deactivated users")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email to admins: {e}"))
