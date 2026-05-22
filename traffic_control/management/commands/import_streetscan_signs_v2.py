"""Management command to import V2 traffic sign CSV data into the database."""
from __future__ import annotations

import os
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from traffic_control.analyze_utils.traffic_sign_data_v2_import import (
    TrafficSignImporterV2,
    VALID_OBJECT_TYPES,
    VALID_PHASES,
)


class Command(BaseCommand):
    """Import V2 traffic sign CSV data (mounts, signs, signposts, additional signs).

    Supports selective execution via --object-type and --phase flags, dry-run
    simulation, and resuming after a partial failure via --resume.
    """

    help = (
        "Import V2 traffic sign CSV data into the database. "
        "Use --object-type and --phase to restrict which object types and "
        "operations are executed."
    )

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
            help="Path to the mount CSV file.",
        )
        parser.add_argument(
            "-sf",
            "--sign-file",
            type=str,
            required=True,
            help="Path to the sign CSV file (contains traffic signs, signposts and additional signs).",
        )
        parser.add_argument(
            "-d",
            "--delimiter",
            type=str,
            default=",",
            help="CSV delimiter character (default: ,).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help=(
                "Simulate the import without writing to the database. "
                "A run log row is still written with is_dry_run=True."
            ),
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            default=False,
            help=(
                "Skip source_ids already recorded as successfully processed in previous "
                "non-dry-run executions for the same file pair."
            ),
        )
        parser.add_argument(
            "--object-type",
            dest="object_types",
            action="append",
            choices=list(VALID_OBJECT_TYPES),
            metavar="OBJECT_TYPE",
            help=(
                f"Object type to process. May be repeated. "
                f"Valid values: {', '.join(VALID_OBJECT_TYPES)}. "
                f"If omitted, all four object types are processed in dependency order."
            ),
        )
        parser.add_argument(
            "--phase",
            dest="phases",
            action="append",
            choices=list(VALID_PHASES),
            metavar="PHASE",
            help=(
                f"Operation phase to run. May be repeated. "
                f"Valid values: {', '.join(VALID_PHASES)}. "
                f"If omitted, all three phases are run."
            ),
        )

    def _validate_file(self, path: str, label: str) -> bool:
        """Check that a file path exists and is readable.

        Args:
            path (str): File system path to check.
            label (str): Human-readable label used in the error message.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"{label} not found: {path}"))
            return False
        return True

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the V2 import command.

        Args:
            *args: Positional arguments (unused).
            **options: Parsed command options.
        """
        mount_file: str = options["mount_file"]
        sign_file: str = options["sign_file"]
        delimiter: str = options["delimiter"]
        dry_run: bool = options["dry_run"]
        resume: bool = options["resume"]

        # Default to all object types / phases when none specified.
        object_types: list[str] = options["object_types"] or list(VALID_OBJECT_TYPES)
        phases: list[str] = options["phases"] or list(VALID_PHASES)

        if not self._validate_file(mount_file, "Mount file"):
            return
        if not self._validate_file(sign_file, "Sign file"):
            return

        self.stdout.write(self.style.SUCCESS("Starting V2 traffic sign import"))
        self.stdout.write(f"  mount_file   : {mount_file}")
        self.stdout.write(f"  sign_file    : {sign_file}")
        self.stdout.write(f"  delimiter    : '{delimiter}'")
        self.stdout.write(f"  dry_run      : {dry_run}")
        self.stdout.write(f"  resume       : {resume}")
        self.stdout.write(f"  object_types : {object_types}")
        self.stdout.write(f"  phases       : {phases}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes will be performed"))

        importer = TrafficSignImporterV2(
            mount_file=mount_file,
            sign_file=sign_file,
            object_types=object_types,
            phases=phases,
            dry_run=dry_run,
            resume=resume,
            delimiter=delimiter,
        )

        summary = importer.run()

        self._print_summary(summary)

    def _print_summary(self, summary: dict[str, Any]) -> None:
        """Print a human-readable summary of the import run to stdout.

        Args:
            summary (dict[str, Any]): Summary dict returned by TrafficSignImporterV2.run().
        """
        self.stdout.write(self.style.SUCCESS("\n--- Import summary ---"))
        self.stdout.write(f"  object_types : {summary.get('object_types')}")
        self.stdout.write(f"  phases       : {summary.get('phases')}")
        self.stdout.write(f"  dry_run      : {summary.get('dry_run')}")
        details: list = summary.get("details", [])
        warnings = [e for e in details if e.get("level") == "warning"]
        skips = [e for e in details if e.get("level") == "skip"]
        errors = [e for e in details if e.get("level") == "error"]
        self.stdout.write(f"  skipped      : {len(skips)}")
        self.stdout.write(f"  warnings     : {len(warnings)}")
        self.stdout.write(f"  errors       : {len(errors)}")
        if errors:
            self.stdout.write(self.style.ERROR(f"\n  {len(errors)} error(s) occurred:"))
            for entry in errors:
                self.stdout.write(self.style.ERROR(f"    [{entry.get('source_id')}] {entry.get('reason')}"))
        self.stdout.write(self.style.SUCCESS("--- End of summary ---"))
