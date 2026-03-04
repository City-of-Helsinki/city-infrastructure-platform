"""Management command to analyze traffic sign CSV data in V2 format (with status field)."""
import csv
import os
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from traffic_control.analyze_utils.traffic_sign_data_v2 import TrafficSignAnalyzerV2


class Command(BaseCommand):
    """Analyze traffic sign V2 CSV data and generate analysis reports."""

    help = "Analyzes sign input data in V2 format (with status field) and generates analysis reports"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments.

        Args:
            parser (CommandParser): Argument parser to add arguments to.
        """
        parser.add_argument(
            "-mf",
            "--mount-file",
            type=str,
            required=True,
            help="Path to the mount file in CSV format",
        )
        parser.add_argument(
            "-sf",
            "--sign-file",
            type=str,
            required=True,
            help="Path to the sign file in CSV format (contains both traffic signs and additional signs)",
        )
        parser.add_argument(
            "-pmf",
            "--previous-mount-file",
            type=str,
            required=True,
            help="Path to the previous mount file in CSV format (for tracking source_ids from previous import)",
        )
        parser.add_argument(
            "-psf",
            "--previous-sign-file",
            type=str,
            required=True,
            help="Path to the previous sign file in CSV format (for tracking source_ids from previous import)",
        )
        parser.add_argument(
            "-o",
            "--output-dir",
            type=str,
            default="streetdata_import_results_v2",
            help="Path to the output directory where analysis reports are saved"
            " (default: streetdata_import_results_v2)",
        )
        parser.add_argument(
            "-d",
            "--delimiter",
            type=str,
            default=",",
            help="CSV delimiter character (default: ,)",
        )

    def _validate_file(self, path: str, label: str) -> bool:
        """Check that a file path exists, writing an error message if not.

        Args:
            path (str): File system path to check.
            label (str): Human-readable label used in the error message.

        Returns:
            bool: True if file exists, False otherwise.
        """
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"{label} not found: {path}"))
            return False
        return True

    def _collect_invalid_codes(self, reports: list[dict]) -> set[str]:
        """Collect invalid device type codes from the analysis reports.

        Args:
            reports (list[dict]): List of report dicts produced by the analyzer.

        Returns:
            set[str]: Set of invalid device type code strings.
        """
        invalid_codes: set[str] = set()
        for report in reports:
            if report["REPORT_TYPE"] == "INVALID DEVICE TYPE CODES":
                for result in report["results"]:
                    code = result.get("invalid_code")
                    if code:
                        invalid_codes.add(code)
        return invalid_codes

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command to analyze traffic sign data.

        Args:
            *args: Positional arguments.
            **options: Command options including mount_file, sign_file, output_dir, delimiter.
        """
        mount_file = options["mount_file"]
        sign_file = options["sign_file"]
        previous_mount_file = options["previous_mount_file"]
        previous_sign_file = options["previous_sign_file"]

        files = [
            (mount_file, "Mount file"),
            (sign_file, "Sign file"),
            (previous_mount_file, "Previous mount file"),
            (previous_sign_file, "Previous sign file"),
        ]
        if not all(self._validate_file(path, label) for path, label in files):
            return None

        output_dir = options["output_dir"]
        delimiter = options["delimiter"]

        os.makedirs(output_dir, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("Analyzing traffic sign data V2..."))
        self.stdout.write(f"  Mount file: {mount_file}")
        self.stdout.write(f"  Sign file: {sign_file}")
        self.stdout.write(f"  Previous mount file: {previous_mount_file}")
        self.stdout.write(f"  Previous sign file: {previous_sign_file}")
        self.stdout.write(f"  Delimiter: '{delimiter}'")
        self.stdout.write(f"  Output directory: {output_dir}")

        analyzer = TrafficSignAnalyzerV2(
            mount_file,
            sign_file,
            previous_mount_file=previous_mount_file,
            previous_sign_file=previous_sign_file,
            delimiter=delimiter,
            output_dir=output_dir,
        )

        self.stdout.write(self.style.SUCCESS("Generating analysis reports..."))
        reports = analyzer.analyze()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for report in reports:
            report_type = report["REPORT_TYPE"]
            results = report["results"]
            filename = f"{report_type.lower().replace(' ', '_')}_analysis_{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)
            self._write_report_to_csv(filepath, results, report_type)
            self.stdout.write(f"  ✓ {report_type}: {len(results)} entries -> {filename}")

        invalid_codes = self._collect_invalid_codes(reports)
        if invalid_codes:
            self.stdout.write(self.style.WARNING(f"\n⚠ Found {len(invalid_codes)} invalid device type codes:"))
            for code in sorted(invalid_codes):
                self.stdout.write(self.style.WARNING(f"    - {code}"))

        self.stdout.write(self.style.SUCCESS(f"\n✓ Analysis complete! Reports saved to: {output_dir}"))

    def _write_report_to_csv(self, filepath: str, results: list[dict], report_type: str) -> None:
        """Write report results to CSV file.

        Args:
            filepath (str): Path to output CSV file.
            results (list[dict]): List of result dictionaries to write.
            report_type (str): Name of the report type for empty file indication.
        """
        if not results:
            # Write empty file with header indicating no results
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["REPORT_TYPE", "STATUS"])
                writer.writerow([report_type, "No results found"])
            return

        # Collect all unique headers from all results (in case results have varying fields)
        headers = []
        seen_headers = set()
        for result in results:
            for key in result.keys():
                if key not in seen_headers:
                    headers.append(key)
                    seen_headers.add(key)

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
