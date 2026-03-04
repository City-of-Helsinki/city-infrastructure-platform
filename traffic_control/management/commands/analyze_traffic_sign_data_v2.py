"""Management command to analyze traffic sign CSV data in V2 format (with status field)."""
import csv
import os
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignAnalyzerV2


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
            "-o",
            "--output-dir",
            type=str,
            default="streetdata_import_results_v2",
            help="Path to the output directory where analysis reports are saved (default: streetdata_import_results_v2)",
        )
        parser.add_argument(
            "-d",
            "--delimiter",
            type=str,
            default=",",
            help="CSV delimiter character (default: ,)",
        )

    def handle(self, *args: Any, **options: dict) -> None:
        """Execute the command to analyze traffic sign data.

        Args:
            *args: Positional arguments.
            **options: Command options including mount_file, sign_file, output_dir, delimiter.
        """
        mount_file = options["mount_file"]
        if not os.path.exists(mount_file):
            self.stderr.write(self.style.ERROR(f"Mount file not found: {mount_file}"))
            return None

        sign_file = options["sign_file"]
        if not os.path.exists(sign_file):
            self.stderr.write(self.style.ERROR(f"Sign file not found: {sign_file}"))
            return None

        output_dir = options["output_dir"]
        delimiter = options["delimiter"]

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("Analyzing traffic sign data V2..."))
        self.stdout.write(f"  Mount file: {mount_file}")
        self.stdout.write(f"  Sign file: {sign_file}")
        self.stdout.write(f"  Delimiter: '{delimiter}'")
        self.stdout.write(f"  Output directory: {output_dir}")

        # Create analyzer
        analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=delimiter)

        # Generate all reports
        self.stdout.write(self.style.SUCCESS("Generating analysis reports..."))
        reports = analyzer.analyze()

        # Write each report to a separate CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for report in reports:
            report_type = report["REPORT_TYPE"]
            results = report["results"]

            # Create filename from report type
            filename = f"{report_type.lower().replace(' ', '_')}_analysis_{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)

            self._write_report_to_csv(filepath, results, report_type)
            self.stdout.write(f"  ✓ {report_type}: {len(results)} entries -> {filename}")

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
