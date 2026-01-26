import os
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from traffic_control.analyze_utils.plan_geometry_importer import PlanGeometryImporter
from traffic_control.models import PlanGeometryImportLog


class Command(BaseCommand):
    """Django management command to import plan geometries from CSV files."""

    help = "Import plan geometries from CSV file with WKT MultiPolygon data"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the CSV file containing plan geometries",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="plan_geometry_import_results",
            help="Directory for output CSV reports (default: plan_geometry_import_results)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Run without updating database",
        )
        parser.add_argument(
            "--no-csv",
            action="store_true",
            dest="no_csv",
            default=False,
            help="Skip CSV report generation",
        )

    def _print_update_details(self, results: List[Dict], summary: Dict[str, int], dry_run: bool) -> None:
        """Print detailed update information for successful updates.

        Args:
            results (List[Dict]): List of all results.
            summary (Dict[str, int]): Summary statistics.
            dry_run (bool): Whether this was a dry-run.
        """
        if dry_run or summary["updated"] == 0:
            return

        updated_results = [r for r in results if r.get("result_type") == "success" and "update_details" in r]
        if not updated_results:
            return

        self.stdout.write(self.style.SUCCESS("\n=== Update Details ==="))
        for result in updated_results[:10]:
            details = result["update_details"]
            self.stdout.write(f"\nCSV Row {details['csv_row']}:")
            self.stdout.write(f"  Plan ID: {details['plan_id']}")
            self.stdout.write(f"  Diary Number: {details['diary_number']}")
            self.stdout.write("  Fields updated:")
            for field_change in details["fields_changed"]:
                self.stdout.write(
                    f"    - {field_change['field']}: {field_change['old_value']} → {field_change['new_value']}"
                )
        if len(updated_results) > 10:
            self.stdout.write(
                f"\n  (Showing first 10 of {len(updated_results)} updates. " f"See database log for complete details)"
            )

    def _print_error_breakdown(self, results: List[Dict]) -> None:
        """Print breakdown of errors by type.

        Args:
            results (List[Dict]): List of all results.
        """
        error_types = {}
        for result in results:
            result_type = result.get("result_type")
            if result_type not in ("success", "skipped_no_changes"):
                error_types[result_type] = error_types.get(result_type, 0) + 1

        if error_types:
            self.stdout.write("\n=== Error Breakdown ===")
            for error_type, count in sorted(error_types.items()):
                self.stdout.write(f"  {error_type}: {count}")

    def _print_summary(
        self,
        summary: Dict[str, int],
        results: List[Dict],
        log_id: str,
        no_csv: bool,
        output_dir: str,
    ) -> None:
        """Print import summary statistics.

        Args:
            summary (Dict[str, int]): Summary statistics.
            results (List[Dict]): List of all results.
            log_id (str): Database log entry ID.
            no_csv (bool): Whether CSV generation was skipped.
            output_dir (str): Output directory path.
        """
        self.stdout.write(self.style.SUCCESS("\n=== Import Summary ==="))
        self.stdout.write(f"Total rows processed: {summary['total_rows']}")
        self.stdout.write(self.style.SUCCESS(f"Successfully updated: {summary['updated']}"))

        skipped_count = sum(1 for r in results if r.get("result_type") == "skipped_no_changes")
        if skipped_count > 0:
            self.stdout.write(f"Skipped (no changes): {skipped_count}")

        if summary["errors"] > 0:
            self.stdout.write(self.style.WARNING(f"Errors encountered: {summary['errors']}"))

        self.stdout.write(f"\nDetailed results saved to database (Log ID: {log_id})")
        if not no_csv:
            self.stdout.write(f"CSV reports saved to: {output_dir}")
        else:
            self.stdout.write("CSV reports were not generated (--no-csv flag was set)")

    def handle(self, *args: Any, **options: Dict[str, Any]) -> None:
        """Execute the import process.

        Orchestrates the plan geometry import workflow:
        1. Validates file exists
        2. Creates database log entry
        3. Parses CSV file
        4. Validates geometries and matches Plans
        5. Updates database (or simulates in dry-run)
        6. Generates CSV reports
        7. Updates log with results
        8. Displays summary statistics

        Args:
            *args: Variable length argument list (unused).
            **options: Command-line options including file, output_dir, dry_run, and no_csv.
        """
        file_path: str = options["file"]
        output_dir: str = options["output_dir"]
        dry_run: bool = options["dry_run"]
        no_csv: bool = options["no_csv"]

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path=os.path.abspath(file_path),
            output_dir=os.path.abspath(output_dir),
            dry_run=dry_run,
        )

        try:
            self.stdout.write(self.style.SUCCESS(f"Starting plan geometry import from: {file_path}"))
            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN MODE - No database changes will be made"))

            importer = PlanGeometryImporter(file_path)
            self.stdout.write("Parsing CSV file...")
            importer.parse_csv()

            if not importer.results:
                self.stdout.write(self.style.WARNING("No data rows found in CSV"))
                log.end_time = timezone.now()
                log.results = []
                log.save()
                return

            self.stdout.write("Validating geometries and matching plans...")
            importer.validate_and_process_rows()

            self.stdout.write("Updating plans..." if not dry_run else "Simulating updates...")
            summary = importer.update_plans(dry_run=dry_run)

            if not no_csv:
                self.stdout.write(f"Generating CSV reports to: {output_dir}")
                importer.generate_csv_reports(output_dir)
            else:
                self.stdout.write("Skipping CSV report generation (--no-csv flag set)")

            results = importer.get_results()
            log.end_time = timezone.now()
            log.results = results
            log.save()

            self._print_summary(summary, results, str(log.id), no_csv, output_dir)
            self._print_update_details(results, summary, dry_run)
            self._print_error_breakdown(results)

        except Exception as e:
            # Ensure log is updated even on error
            log.end_time = timezone.now()
            if hasattr(importer, "results") and importer.results:
                log.results = importer.get_results()
            log.save()

            self.stderr.write(self.style.ERROR(f"Error during import: {str(e)}"))
            raise
