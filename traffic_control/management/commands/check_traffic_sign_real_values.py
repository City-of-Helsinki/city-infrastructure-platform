"""Management command for checking that TrafficSignReal values match their device type code."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.management.base import CommandError, CommandParser
from django.db import DatabaseError
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.analyze_utils.traffic_sign_value_check import (
    count_sorted,
    get_admin_url,
    load_families_from_json,
    problems_as_dicts,
    SignFix,
    TrafficSignValueChecker,
)
from traffic_control.constants import SignValueFamily
from traffic_control.models import TrafficSignValueCheckRunInfo
from users.utils import get_system_user

DEFAULT_MAX_DETAILS = 10


class Command(TrackableCommand):
    """Django management command to check TrafficSignReal values against their traffic sign code."""

    help = (
        "Checks that TrafficSignReal values are in line with their device type code. "
        "Signs using a subcode must have the value defined for that subcode and signs using a generic "
        "code must not have a value belonging to any of the code's subcodes. Nothing is modified."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.

        Returns:
            None
        """
        parser.add_argument(
            "--codes",
            nargs="+",
            default=None,
            help="Generic codes to limit the check to, e.g. 'C21'. All known codes are checked by default.",
        )
        parser.add_argument(
            "--output-csv",
            type=str,
            default=None,
            help="Path of a CSV file to write the found problems into.",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            dest="include_inactive",
            default=False,
            help=(
                "Also check traffic sign reals that are not in use, meaning soft-deleted signs "
                "and signs whose lifecycle is not active or temporarily active."
            ),
        )
        parser.add_argument(
            "--extra-families",
            type=str,
            default=None,
            dest="extra_families",
            help=(
                "Path of a JSON file with additional code families to check. The file contains an "
                'object keyed by generic code, e.g. {"C21": {"default_value": "2.2", "subcodes": '
                '{"C21_2": "2.0"}}}. Both "default_value" and "subcodes" are optional. Families '
                "override built-in families that use the same generic code."
            ),
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            dest="fix",
            default=False,
            help=(
                "Correct the found problems. Signs using a subcode but missing a value get the "
                "value of their subcode and signs using a generic code are moved to the subcode "
                "whose value they carry. Signs that have the wrong value for their own subcode "
                "are left alone, as either the value or the device type could be the wrong one."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Report the fixes that would be made without updating the database.",
        )
        parser.add_argument(
            "--max-details",
            type=int,
            default=DEFAULT_MAX_DETAILS,
            help=(
                "Maximum number of individual problems to print with their expected values "
                f"(default: {DEFAULT_MAX_DETAILS}, 0 prints all)."
            ),
        )

    def handle(
        self,
        *,
        codes: Optional[List[str]],
        output_csv: Optional[str],
        include_inactive: bool,
        extra_families: Optional[str],
        fix: bool,
        dry_run: bool,
        max_details: int,
        **_kwargs: dict,
    ) -> None:
        """Execute the value check.

        Orchestrates the check workflow:
        1. Loads possible extra code families from a JSON file
        2. Builds the checker for the selected traffic sign code families
        3. Warns about declared codes that have no device type in the database
        4. Checks the traffic sign reals
        5. Prints a summary, optionally fixes the problems and optionally writes a CSV report
        6. Records the run in the database

        Args:
            codes (Optional[List[str]]): Generic codes to limit the check to, or None for all.
            output_csv (Optional[str]): Path to write the CSV report to, or None to skip it.
            include_inactive (bool): Whether to also check signs that are not in use.
            extra_families (Optional[str]): Path of a JSON file with additional code families.
            fix (bool): Whether to correct the found problems.
            dry_run (bool): Whether to only report the fixes without writing them.
            max_details (int): Maximum number of problems to print, 0 prints all of them.
            **_kwargs: Remaining command options (unused).

        Returns:
            None

        Raises:
            CommandError: If an unknown generic code is given with --codes or the extra families
                file is missing or invalid.
        """
        start_time = timezone.now()
        try:
            checker = TrafficSignValueChecker(
                codes=codes,
                include_inactive=include_inactive,
                extra_families=self._load_extra_families(extra_families),
            )
        except ValueError as error:
            raise CommandError(str(error))

        self._print_missing_device_types(checker.get_missing_device_type_codes())

        self.stdout.write("Checking traffic sign real values...")
        checker.check_signs()

        self._print_summary(checker)
        self._print_problem_details(checker, max_details)
        fixes = self._fix_problems(checker, fix=fix, dry_run=dry_run, max_details=max_details)
        self._write_csv_report(checker, fixes, output_csv=output_csv, dry_run=dry_run)
        self._save_run_info(checker, fixes, start_time, fix=fix, dry_run=dry_run)

    def _save_run_info(
        self,
        checker: TrafficSignValueChecker,
        fixes: Optional[List[SignFix]],
        start_time: datetime,
        *,
        fix: bool,
        dry_run: bool,
    ) -> None:
        """Record the run in the database.

        The checker does not know about the run info model, so the command builds and saves the
        record itself. A failure to save is reported but does not fail the run, as the found
        problems have already been printed and any fixes have already been written.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            fixes (Optional[List[SignFix]]): Fixes that were planned, or None when fixing was
                not requested.
            start_time (datetime): Time the run was started.
            fix (bool): Whether correcting the problems was requested.
            dry_run (bool): Whether the fixes were only planned.

        Returns:
            None
        """
        counts = checker.get_run_counts(fixes)
        database_update = counts["fixed_count"] > 0 and fix and not dry_run

        try:
            TrafficSignValueCheckRunInfo.objects.create(
                start_time=start_time,
                end_time=timezone.now(),
                checked_codes=sorted(checker.checked_codes),
                problems=problems_as_dicts(checker.problems, fixes, dry_run),
                database_update=database_update,
                **counts,
            )
        except DatabaseError as error:
            self.stdout.write(self.style.ERROR(f"Could not save the run info: {error}"))

    def _fix_problems(
        self,
        checker: TrafficSignValueChecker,
        *,
        fix: bool,
        dry_run: bool,
        max_details: int,
    ) -> Optional[List[SignFix]]:
        """Correct the found problems when --fix or --dry-run is given.

        A dry run wins over --fix, so giving both flags never writes anything.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            fix (bool): Whether correcting the problems was requested.
            dry_run (bool): Whether to only plan the fixes without writing them.
            max_details (int): Maximum number of fixes to print, 0 prints all of them.

        Returns:
            Optional[List[SignFix]]: The planned fixes, or None when fixing was not requested.
        """
        if not (fix or dry_run) or not checker.problems:
            return None

        fixes = checker.apply_fixes(user=get_system_user(), dry_run=dry_run)
        self._print_fix_summary(fixes, dry_run, max_details)
        return fixes

    def _print_fix_summary(self, fixes: List[SignFix], dry_run: bool, max_details: int) -> None:
        """Print what was fixed, or what would be fixed on a dry run.

        Args:
            fixes (List[SignFix]): Planned fixes, including the skipped ones.
            dry_run (bool): Whether the fixes were only planned.
            max_details (int): Maximum number of fixes to print, 0 prints all of them.

        Returns:
            None
        """
        applied = [fix for fix in fixes if not fix.is_skipped]
        skipped = [fix for fix in fixes if fix.is_skipped]

        title = "=== Fixes That Would Be Made ===" if dry_run else "=== Applied Fixes ==="
        self.stdout.write(self.style.SUCCESS(f"\n{title}"))

        category_counts = count_sorted(fix.problem.error_category for fix in applied)
        for category, count in category_counts.items():
            self.stdout.write(f"  {category}: {count}")

        self._print_fix_details(applied, max_details)
        self._print_skipped_fixes(skipped, max_details)

        verb = "would be fixed" if dry_run else "fixed"
        self.stdout.write(self.style.SUCCESS(f"\n{len(applied)} traffic sign reals {verb}."))

    def _print_fix_details(self, fixes: List[SignFix], max_details: int) -> None:
        """Print the individual changes that are made.

        Args:
            fixes (List[SignFix]): Fixes that can be applied.
            max_details (int): Maximum number of fixes to print, 0 prints all of them.

        Returns:
            None
        """
        if not fixes:
            return

        shown_fixes = fixes if max_details <= 0 else fixes[:max_details]
        self.stdout.write("\nFix details:")
        for fix in shown_fixes:
            self.stdout.write(f"  {fix.problem.sign_id} {fix.description}")

        hidden_count = len(fixes) - len(shown_fixes)
        if hidden_count:
            self.stdout.write(f"  (and {hidden_count} more, use --max-details 0 to see all)")

    def _print_skipped_fixes(self, fixes: List[SignFix], max_details: int) -> None:
        """Print the fixes that cannot be applied and why.

        Args:
            fixes (List[SignFix]): Fixes that are skipped.
            max_details (int): Maximum number of fixes to print, 0 prints all of them.

        Returns:
            None
        """
        if not fixes:
            return

        shown_fixes = fixes if max_details <= 0 else fixes[:max_details]
        self.stdout.write(self.style.WARNING(f"\nSkipped fixes ({len(fixes)}):"))
        for fix in shown_fixes:
            self.stdout.write(f"  {fix.problem.sign_id} {fix.description}")

        hidden_count = len(fixes) - len(shown_fixes)
        if hidden_count:
            self.stdout.write(f"  (and {hidden_count} more, use --max-details 0 to see all)")

    @staticmethod
    def _load_extra_families(path: Optional[str]) -> Optional[Dict[str, SignValueFamily]]:
        """Load extra code families from a JSON file when one is given.

        Args:
            path (Optional[str]): Path of the JSON file, or None when no extra families are wanted.

        Returns:
            Optional[Dict[str, SignValueFamily]]: Extra families by generic code, or None.

        Raises:
            ValueError: If the file cannot be read or contains invalid family definitions.
        """
        return load_families_from_json(path) if path else None

    def _print_missing_device_types(self, missing_codes: List[str]) -> None:
        """Warn about declared codes that have no device type in the database.

        Args:
            missing_codes (List[str]): Codes that have no matching TrafficControlDeviceType row.

        Returns:
            None
        """
        if missing_codes:
            self.stdout.write(self.style.WARNING(f"No device type found for code(s): {', '.join(missing_codes)}"))

    def _print_summary(self, checker: TrafficSignValueChecker) -> None:
        """Print a summary of the check.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS("\n=== Value Check Summary ==="))
        self.stdout.write(f"Traffic sign reals checked: {checker.checked_count}")

        if not checker.problems:
            self.stdout.write(self.style.SUCCESS("No value problems found."))
            return

        titles = {
            "error_category": "Problems by error category",
            "generic_code": "Problems by generic code",
        }
        for key, title in titles.items():
            self.stdout.write(f"\n{title}:")
            for name, count in checker.get_summary()[key].items():
                self.stdout.write(f"  {name}: {count}")

        self.stdout.write("\nProblems by device type code:")
        for code, info in checker.get_code_summary().items():
            self.stdout.write(f"  {code}: {info['count']} ({self._format_expectation(info)})")

        self.stdout.write(
            self.style.WARNING(f"\nFound {len(checker.problems)} traffic sign reals with a value problem.")
        )

    @staticmethod
    def _format_expectation(code_info: Dict[str, Any]) -> str:
        """Describe what value a device type code is expected to have.

        Args:
            code_info (Dict[str, Any]): Device type code info from
                TrafficSignValueChecker.get_code_summary().

        Returns:
            str: Description of the expected value of the code.
        """
        if code_info["is_generic"]:
            return "generic code, expected value: any value that is not a subcode value"

        return f"expected value: {code_info['expected_value']}"

    def _print_problem_details(self, checker: TrafficSignValueChecker, max_details: int) -> None:
        """Print individual problems with their current and expected values.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            max_details (int): Maximum number of problems to print, 0 prints all of them.

        Returns:
            None
        """
        if not checker.problems:
            return

        shown_problems = checker.problems if max_details <= 0 else checker.problems[:max_details]

        self.stdout.write("\nProblem details:")
        for problem in shown_problems:
            self.stdout.write(f"\n  {problem.sign_id}")
            self.stdout.write(f"    {problem.description}")
            self.stdout.write(f"    Source: {problem.source_name or '-'} / {problem.source_id or '-'}")
            self.stdout.write(f"    Link to edit: {get_admin_url(problem.sign_id)}")

        hidden_count = len(checker.problems) - len(shown_problems)
        if hidden_count:
            self.stdout.write(
                f"\n  (Showing first {len(shown_problems)} of {len(checker.problems)} problems. "
                "Use --max-details 0 or --output-csv for the complete list)"
            )

    def _write_csv_report(
        self,
        checker: TrafficSignValueChecker,
        fixes: Optional[List[SignFix]],
        *,
        output_csv: Optional[str],
        dry_run: bool,
    ) -> None:
        """Write a CSV report of the found problems when requested.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            fixes (Optional[List[SignFix]]): Fixes that were planned, or None when fixing was
                not requested.
            output_csv (Optional[str]): Path to write the report to, or None to skip it.
            dry_run (bool): Whether the fixes were only planned.

        Returns:
            None
        """
        if not output_csv or not checker.problems:
            return

        checker.write_csv_report(output_csv, fixes=fixes, dry_run=dry_run)
        self.stdout.write(f"Wrote {len(checker.problems)} rows to {output_csv}")
