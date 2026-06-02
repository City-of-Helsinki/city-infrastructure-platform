"""Management command to import V2 traffic sign CSV data into the database."""
import logging
import os
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from traffic_control.analyze_utils.traffic_sign_data_v2_import import (
    TrafficSignImporterV2,
    VALID_OBJECT_TYPES,
    VALID_PHASES,
)
from users.utils import get_system_user


class Command(BaseCommand):
    """Import V2 traffic sign CSV data (mounts, signs, signposts, additional signs).

    Supports selective execution via --object-type and --phase flags, dry-run
    simulation, and --force-update to bypass the default resume behaviour.
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
                "A run log row is still written with dry_run=True."
            ),
        )
        parser.add_argument(
            "--force-update",
            dest="force_update",
            action="store_true",
            default=False,
            help=(
                "Re-process all rows, even those already recorded as successfully processed "
                "in previous non-dry-run executions for the same file pair. "
                "By default, already-processed source_ids are skipped (resume behaviour)."
            ),
        )
        parser.add_argument(
            "--batch-size",
            dest="batch_size",
            type=int,
            default=1000,
            help=(
                "Number of records per bulk_create / bulk_update batch. "
                "Lower values reduce peak memory usage at the cost of more DB round-trips. "
                "Default: 1000."
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
        force_update: bool = options["force_update"]
        batch_size: int = options["batch_size"]

        # Default to all object types / phases when none specified.
        object_types: list[str] = options["object_types"] or list(VALID_OBJECT_TYPES)
        phases: list[str] = options["phases"] or list(VALID_PHASES)

        if not self._validate_file(mount_file, "Mount file"):
            return
        if not self._validate_file(sign_file, "Sign file"):
            return

        user = get_system_user()

        # Forward importer logger output to management command stdout.
        # verbosity 0 → WARNING+, 1 (default) → INFO+, 2/3 → DEBUG+
        verbosity: int = options.get("verbosity", 1)
        if verbosity == 0:
            log_level = logging.WARNING
        elif verbosity >= 2:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        importer_logger = logging.getLogger("traffic_control.analyze_utils.traffic_sign_data_v2_import")
        _stream_handler = logging.StreamHandler(self.stdout)
        _stream_handler.setLevel(log_level)
        importer_logger.addHandler(_stream_handler)
        importer_logger.setLevel(log_level)

        self.stdout.write(self.style.SUCCESS("Starting V2 traffic sign import"))
        self.stdout.write(f"  mount_file   : {mount_file}")
        self.stdout.write(f"  sign_file    : {sign_file}")
        self.stdout.write(f"  delimiter    : '{delimiter}'")
        self.stdout.write(f"  dry_run      : {dry_run}")
        self.stdout.write(f"  force_update : {force_update}")
        self.stdout.write(f"  batch_size   : {batch_size}")
        self.stdout.write(f"  object_types : {object_types}")
        self.stdout.write(f"  phases       : {phases}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no database writes will be performed"))
        if force_update:
            self.stdout.write(self.style.WARNING("FORCE UPDATE — all rows will be re-processed"))

        importer = TrafficSignImporterV2(
            mount_file=mount_file,
            sign_file=sign_file,
            object_types=object_types,
            phases=phases,
            dry_run=dry_run,
            force_update=force_update,
            delimiter=delimiter,
            batch_size=batch_size,
            user=user,
        )

        summary = importer.run()

        self.stdout.write(f"  preprocessing: {importer._preprocessing_duration_s:.2f}s (in phase_durations)")
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

        phase_results: dict = summary.get("phase_results", {})
        if phase_results:
            self.stdout.write("\n  Results per object type / phase:")
            for object_type, phases in phase_results.items():
                for phase, counts in phases.items():
                    duration = counts.pop("duration_s", None)
                    counts_str = "  ".join(f"{k}={v}" for k, v in counts.items())
                    duration_str = f"  ({duration}s)" if duration is not None else ""
                    self.stdout.write(f"    {object_type:<20} {phase:<12} {counts_str}{duration_str}")

        details: list = summary.get("details", [])
        warnings = [e for e in details if e.get("level") == "warning"]
        skips = [e for e in details if e.get("level") == "skip"]
        errors = [e for e in details if e.get("level") == "error"]
        self.stdout.write(f"\n  skipped      : {len(skips)}")
        self.stdout.write(f"  warnings     : {len(warnings)}")
        self.stdout.write(f"  errors       : {len(errors)}")
        if errors:
            self.stdout.write(self.style.ERROR(f"\n  {len(errors)} error(s) occurred:"))
            for entry in errors:
                self.stdout.write(self.style.ERROR(f"    [{entry.get('source_id')}] {entry.get('reason')}"))
        self.stdout.write(self.style.SUCCESS("--- End of summary ---"))
