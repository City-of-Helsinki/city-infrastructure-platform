"""Management command for checking that TrafficSignReal values match their device type code."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.management.base import CommandError, CommandParser
from django.db import DatabaseError
from django.utils import timezone

from command_tracker.management.trackable_command import TrackableCommand
from traffic_control.analyze_utils.traffic_sign_value_check import (
    get_admin_url,
    load_families_from_json,
    results_as_dicts,
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

    def handle(self, *args: Any, **options: Dict[str, Any]) -> None:
        """Execute the value check.

        Orchestrates the check workflow:
        1. Loads possible extra code families from a JSON file
        2. Builds the checker for the selected traffic sign code families
        3. Warns about declared codes that have no device type in the database
        4. Checks the traffic sign reals
        5. Prints a summary, optionally fixes the problems and optionally writes a CSV report
        6. Records the run in the database

        Args:
            *args: Variable length argument list (unused).
            **options: Command-line options including codes, extra_families, output_csv,
                include_inactive, fix and dry_run.

        Returns:
            None

        Raises:
            CommandError: If an unknown generic code is given with --codes or the extra families
                file is missing or invalid.
        """
        start_time = timezone.now()
        try:
            checker = TrafficSignValueChecker(
                codes=options["codes"],
                include_inactive=options["include_inactive"],
                extra_families=self._load_extra_families(options["extra_families"]),
            )
        except ValueError as error:
            raise CommandError(str(error))

        self._print_missing_device_types(checker.get_missing_device_type_codes())

        self.stdout.write("Checking traffic sign real values...")
        checker.check_signs()

        self._print_summary(checker)
        self._print_problem_details(checker, options["max_details"])
        fixes = self._fix_problems(checker, options)
        self._write_csv_report(checker, options, fixes)
        self._save_run_info(checker, options, fixes, start_time)

    def _save_run_info(
        self,
        checker: TrafficSignValueChecker,
        options: Dict[str, Any],
        fixes: Optional[List[SignFix]],
        start_time: datetime,
    ) -> None:
        """Record the run in the database.

        The checker does not know about the run info model, so the command builds and saves the
        record itself. A failure to save is reported but does not fail the run, as the check
        results have already been printed and any fixes have already been written.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            options (Dict[str, Any]): Command-line options including fix and dry_run.
            fixes (Optional[List[SignFix]]): Fixes that were planned, or None when fixing was
                not requested.
            start_time (datetime): Time the run was started.

        Returns:
            None
        """
        counts = checker.get_run_counts(fixes)
        database_update = counts["fixed_count"] > 0 and options["fix"] and not options["dry_run"]

        try:
            TrafficSignValueCheckRunInfo.objects.create(
                start_time=start_time,
                end_time=timezone.now(),
                checked_codes=sorted(checker.checked_codes),
                problems=results_as_dicts(checker.results, fixes, options["dry_run"]),
                database_update=database_update,
                **counts,
            )
        except DatabaseError as error:
            self.stdout.write(self.style.ERROR(f"Could not save the run info: {error}"))

    def _fix_problems(self, checker: TrafficSignValueChecker, options: Dict[str, Any]) -> Optional[List[SignFix]]:
        """Correct the found problems when --fix or --dry-run is given.

        A dry run wins over --fix, so giving both flags never writes anything.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            options (Dict[str, Any]): Command-line options including fix, dry_run and max_details.

        Returns:
            Optional[List[SignFix]]: The planned fixes, or None when fixing was not requested.
        """
        fixing_requested = options["fix"] or options["dry_run"]
        if not fixing_requested or not checker.results:
            return None

        dry_run = options["dry_run"]
        fixes = checker.apply_fixes(user=get_system_user(), dry_run=dry_run)
        self._print_fix_summary(fixes, dry_run, options["max_details"])
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

        for category, count in self._count_by_category(applied).items():
            self.stdout.write(f"  {category}: {count}")

        self._print_fix_details(applied, max_details)
        self._print_skipped_fixes(skipped, max_details)

        verb = "would be fixed" if dry_run else "fixed"
        self.stdout.write(self.style.SUCCESS(f"\n{len(applied)} traffic sign reals {verb}."))

    @staticmethod
    def _count_by_category(fixes: List[SignFix]) -> Dict[str, int]:
        """Count fixes by the error category they correct.

        Args:
            fixes (List[SignFix]): Fixes to count.

        Returns:
            Dict[str, int]: Fix counts by error category, ordered by the category name.
        """
        counts: Dict[str, int] = {}
        for fix in fixes:
            category = fix.result.error_category
            counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items()))

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
            self.stdout.write(f"  {fix.result.sign_id} {fix.description}")

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
            self.stdout.write(f"  {fix.result.sign_id} {fix.description}")

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
        """Print a summary of the check results.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS("\n=== Value Check Summary ==="))
        self.stdout.write(f"Traffic sign reals checked: {checker.checked_count}")

        if not checker.results:
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
            self.style.WARNING(f"\nFound {len(checker.results)} traffic sign reals with a value problem.")
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
        if not checker.results:
            return

        shown_results = checker.results if max_details <= 0 else checker.results[:max_details]

        self.stdout.write("\nProblem details:")
        for result in shown_results:
            self.stdout.write(f"\n  {result.sign_id}")
            self.stdout.write(f"    {result.description}")
            self.stdout.write(f"    Source: {result.source_name or '-'} / {result.source_id or '-'}")
            self.stdout.write(f"    Link to edit: {get_admin_url(result.sign_id)}")

        hidden_count = len(checker.results) - len(shown_results)
        if hidden_count:
            self.stdout.write(
                f"\n  (Showing first {len(shown_results)} of {len(checker.results)} problems. "
                "Use --max-details 0 or --output-csv for the complete list)"
            )

    def _write_csv_report(
        self,
        checker: TrafficSignValueChecker,
        options: Dict[str, Any],
        fixes: Optional[List[SignFix]],
    ) -> None:
        """Write a CSV report of the found problems when requested.

        Args:
            checker (TrafficSignValueChecker): Checker that has been run.
            options (Dict[str, Any]): Command-line options including output_csv and dry_run.
            fixes (Optional[List[SignFix]]): Fixes that were planned, or None when fixing was
                not requested.

        Returns:
            None
        """
        output_csv = options["output_csv"]
        if not output_csv or not checker.results:
            return

        checker.write_csv_report(output_csv, fixes=fixes, dry_run=options["dry_run"])
        self.stdout.write(f"Wrote {len(checker.results)} rows to {output_csv}")
