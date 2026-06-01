"""V2 traffic sign importer.

Handles create, update and deactivate operations for MountReal, TrafficSignReal,
SignpostReal and AdditionalSignReal based on enriched V2 CSV data.

This module is intentionally kept separate from the analysis pipeline so that
the management command can run an import without triggering the full analysis.
"""

import datetime
import json
import logging
import os
import tempfile
from collections.abc import Callable, Generator
from decimal import Decimal
from typing import Any

from django.core.files import File

from traffic_control.analyze_utils.traffic_sign_data_v2_code_transform import CodeTransformMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2, NUMBER_CODE_PATTERN
from traffic_control.analyze_utils.traffic_sign_data_v2_data_loading import DataLoadingMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_db_builders import DbBuilderMixin
from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.geometry_utils import geometry_is_legit
from traffic_control.models import AdditionalSignReal, MountReal, MountType, Owner, SignpostReal, TrafficSignReal
from traffic_control.models.additional_sign import Color
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier
from traffic_control.models.streetscan_import import StreetScanImportRevertFile, StreetScanImportRun
from traffic_control.models.traffic_sign import LocationSpecifier as SignLocationSpecifier
from users.models import User

logger = logging.getLogger(__name__)

# Valid values for the --object-type and --phase CLI arguments.
VALID_OBJECT_TYPES: tuple[str, ...] = ("mounts", "signs", "signposts", "additional-signs")
VALID_PHASES: tuple[str, ...] = ("create", "update", "deactivate")

# Dependency order — object types must be processed in this sequence.
OBJECT_TYPE_ORDER: tuple[str, ...] = ("mounts", "signs", "signposts", "additional-signs")
# Phase order
PHASE_ORDER: tuple[str, ...] = ("create", "update", "deactivate")

# Mounts are never deactivated; the deactivate phase is silently skipped for them.
_DEACTIVATABLE_OBJECT_TYPES: frozenset[str] = frozenset({"signs", "signposts", "additional-signs"})


class TrafficSignImporterV2(CodeTransformMixin, DbBuilderMixin, DataLoadingMixin):
    """Importer for V2 traffic sign CSV data.

    Inherits only the three mixins required for import:
    - ``CodeTransformMixin``  — code filtering, enrichment and internal-status tagging
    - ``DbBuilderMixin``      — CSV reading and DB lookup map builders
    - ``DataLoadingMixin``    — row grouping by id / type / mount

    Initialisation loads and enriches the CSV rows and builds all DB lookup maps
    needed for FK resolution. Report-only structures (distance maps, location maps,
    status segregation dicts, previous-file comparisons) are intentionally omitted.

    Args:
        mount_file (str): Path to the mount CSV file.
        sign_file (str): Path to the sign CSV file.
        object_types (list[str]): Object types to process. Must be a subset of
            VALID_OBJECT_TYPES. Processed in dependency order regardless of the
            order supplied.
        phases (list[str): Operation phases to run. Must be a subset of
            VALID_PHASES.
        dry_run (bool): When True, no DB writes are performed.
        force_update (bool): When True, the field comparison is bypassed and all
            existing records are updated unconditionally. Default is False.
        delimiter (str): CSV delimiter character.
        batch_size (int): Number of records per bulk_create / bulk_update batch.
            Default 1000.
        user (User | None): User recorded as created_by / updated_by on all written records.
            If None, the fields are left unset (DB default applies).
    """

    def __init__(
        self,
        mount_file: str,
        sign_file: str,
        object_types: list[str],
        phases: list[str],
        dry_run: bool = False,
        force_update: bool = False,
        delimiter: str = ",",
        batch_size: int = 1000,
        user: User | None = None,
    ) -> None:
        """Initialise the importer, enrich them and build DB lookup maps.

        Args:
            mount_file (str): Path to the mount CSV file.
            sign_file (str): Path to the sign CSV file.
            object_types (list[str]): Object types to process.
            phases (list[str]): Operation phases to run.
            dry_run (bool): If True, no DB writes are performed.
            force_update (bool): If True, previously-processed source_ids are not skipped.
                Default False — already-processed rows are skipped (resume behaviour).
            delimiter (str): CSV delimiter character.
            batch_size (int): Number of records per bulk_create / bulk_update batch.
                Default 1000.
            user (User | None): User recorded as created_by / updated_by on written records.
        """
        self.mount_file = mount_file
        self.sign_file = sign_file
        self.dry_run = dry_run
        self.force_update = force_update
        self.delimiter = delimiter
        self.batch_size = batch_size
        self.user = user

        # Normalise and sort by dependency order.
        self.object_types: list[str] = [ot for ot in OBJECT_TYPE_ORDER if ot in object_types]
        self.phases: list[str] = [phase for phase in PHASE_ORDER if phase in phases]

        # --- Owner lookup (fetched first; missing owner is a hard error) ---
        self.default_owner, self.private_owner = self._load_required_owners()

        # --- CSV loading ---
        _t_preprocess_start = datetime.datetime.now()
        self.mount_rows: list[dict] = self._read_csv_file(mount_file, delimiter)
        self.sign_rows: list[dict] = self._read_csv_file(sign_file, delimiter)

        # --- Sign row enrichment (code transforms + internal status) ---
        # These mirror the steps done in TrafficSignAnalyzerV2.__init__ that are
        # needed before import decisions can be made. Report-only steps are omitted.
        # CodeTransformMixin accumulates diagnostics into these lists during enrichment.
        self.filtered_signs: list = []
        self.enriched_signs: list = []
        self.code_replacements: list = []
        self.code_replacement_failures: list = []
        self._add_internal_additional_info_to_rows(self.sign_rows)
        self.sign_rows = self._filter_and_enrich_sign_rows(self.sign_rows)

        # --- DB existence maps (source_id → device_type.code) ---
        # Built before _add_internal_status_to_rows because that method uses them
        # to detect new vs changed vs unchanged rows.
        self.sign_reals_by_source_id: dict = self._build_sign_reals_by_source_id()
        self.additional_sign_reals_by_source_id: dict = self._build_additional_sign_reals_by_source_id()
        self.signpost_reals_by_source_id: dict = self._build_signpost_reals_by_source_id()

        # --- Row grouping by CSV id ---
        self.mounts_by_id: dict = self._get_objects_by_id(self.mount_rows)
        self.all_signs_by_id: dict = self._get_objects_by_id(self.sign_rows)
        self.signs_by_id: dict = self._get_signs_by_id(self.sign_rows)
        self.additional_signs_by_id: dict = self._get_additional_signs_by_id(self.sign_rows)
        self.signposts_by_id: dict = self._get_signposts_by_id(self.sign_rows)

        # --- Device type FK lookup ---
        self.code_to_device_type_id: dict = self._build_code_to_device_type_mapping()

        # --- MountType lookup (by Finnish and English description) ---
        self.mount_types_by_name: dict[str, MountType] = self._build_mount_types_by_name()

        # --- DB PK maps (source_id → db pk) ---
        # Used for update and deactivate FK resolution.
        self.mount_source_id_to_db_id: dict = self._build_mount_source_id_to_db_id()
        self.sign_source_id_to_db_id: dict = self._build_sign_source_id_to_db_id()
        self.additional_sign_source_id_to_db_id: dict = self._build_additional_sign_source_id_to_db_id()
        self.signpost_source_id_to_db_id: dict = self._build_signpost_source_id_to_db_id()

        # Record total preprocessing wall-clock time (CSV I/O + enrichment + DB map builds).
        self._preprocessing_duration_s: float = (datetime.datetime.now() - _t_preprocess_start).total_seconds()
        # Stored in phase_durations under the "preprocessing" key on run_log creation.

        # --- Run log and revert file (populated during run()) ---
        self.run_log: StreetScanImportRun | None = None
        # Revert records are written to a NamedTemporaryFile one line at a time
        # (flushed immediately) so memory consumption is O(1) regardless of the
        # number of records. The file is attached as a StreetScanImportRevertFile
        # at the end of the run and then deleted from the local filesystem.
        # Dry runs never open this file.
        self._revert_tmp: tempfile.NamedTemporaryFile | None = None  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """Execute the import for the configured object types and phases.

        Creates a StreetScanImportRun row before processing begins and updates
        it after every phase. On completion the revert buffer is attached as a
        StreetScanImportRevertFile (skipped for dry runs).

        Returns:
            dict[str, Any]: Summary dict with counts and details entries
                collected during the run.
        """
        logger.info("[TrafficSignImporterV2] Starting import")
        logger.info("  mount_file   : %s", self.mount_file)
        logger.info("  sign_file    : %s", self.sign_file)
        logger.info("  object_types : %s", self.object_types)
        logger.info("  phases       : %s", self.phases)
        logger.info("  dry_run      : %s", self.dry_run)
        logger.info("  force_update : %s", self.force_update)
        logger.info("  mount rows   : %d", len(self.mount_rows))
        logger.info("  sign rows (enriched): %d", len(self.sign_rows))
        logger.info("  signs        : %d", len(self.signs_by_id))
        logger.info("  additional signs: %d", len(self.additional_signs_by_id))
        logger.info("  signposts    : %d", len(self.signposts_by_id))

        summary: dict[str, Any] = {
            "object_types": self.object_types,
            "phases": self.phases,
            "dry_run": self.dry_run,
            "details": [],
        }

        self.run_log = self._create_run_log()

        for object_type in self.object_types:
            self._run_object_type(object_type, summary)

        self._finalise_run_log(summary)

        logger.info("[TrafficSignImporterV2] Import finished")
        return summary

    # ------------------------------------------------------------------
    # Per-object-type dispatch
    # ------------------------------------------------------------------

    def _run_object_type(self, object_type: str, summary: dict[str, Any]) -> None:
        """Run the selected phases for a single object type.

        Args:
            object_type (str): One of VALID_OBJECT_TYPES.
            summary (dict[str, Any]): Mutable summary dict to update with results.
        """
        logger.info("\n[TrafficSignImporterV2] Object type: %s", object_type)
        # Refresh all source_id → DB PK maps once before running any phase for
        # this object type so that objects created by a preceding object type
        # (e.g. mounts created before signs, or signs/signposts created before
        # additional signs) are visible for FK resolution and existence checks.
        self._refresh_db_maps()
        for phase in self.phases:
            if phase == "deactivate" and object_type not in _DEACTIVATABLE_OBJECT_TYPES:
                logger.debug("Skipping phase '%s' — %s are never deactivated", phase, object_type)
                continue
            self._run_phase(object_type, phase, summary)

    def _run_phase(self, object_type: str, phase: str, summary: dict[str, Any]) -> None:  # noqa: C901
        """Dispatch a single object-type / phase combination.

        Args:
            object_type (str): One of VALID_OBJECT_TYPES.
            phase (str): One of VALID_PHASES.
            summary (dict[str, Any]): Mutable summary dict to update with results.
        """
        logger.info("  Phase: %s", phase)
        dispatch: dict[tuple[str, str], Callable[[dict[str, Any]], None]] = {
            ("mounts", "create"): self._create_mounts,
            ("mounts", "update"): self._update_mounts,
            ("signs", "create"): self._create_signs,
            ("signs", "update"): self._update_signs,
            ("signs", "deactivate"): self._deactivate_signs,
            ("signposts", "create"): self._create_signposts,
            ("signposts", "update"): self._update_signposts,
            ("signposts", "deactivate"): self._deactivate_signposts,
            ("additional-signs", "create"): self._create_additional_signs,
            ("additional-signs", "update"): self._update_additional_signs,
            ("additional-signs", "deactivate"): self._deactivate_additional_signs,
        }
        handler = dispatch.get((object_type, phase))
        if handler is None:
            logger.warning("No handler for (%s, %s) — skipping", object_type, phase)
            return
        start = datetime.datetime.now()
        handler(summary)
        duration_s = (datetime.datetime.now() - start).total_seconds()
        phase_result = summary.get("phase_results", {}).get(object_type, {}).get(phase)
        if phase_result is not None:
            phase_result["duration_s"] = round(duration_s, 2)

    # ------------------------------------------------------------------
    # DB map refresh
    # ------------------------------------------------------------------

    def _refresh_db_maps(self) -> None:
        """Rebuild all source_id → DB PK lookup maps from the current DB state.

        Called once per object type in ``_run_object_type`` before any phase
        runs, so that objects created by a preceding object type in the same run
        are visible for FK resolution and existence checks.

        The maps are also built during ``__init__`` so that direct calls to
        individual phase methods (e.g. in tests) work without going through
        ``run()`` / ``_run_object_type``.
        """
        self.mount_source_id_to_db_id = self._build_mount_source_id_to_db_id()
        self.sign_source_id_to_db_id = self._build_sign_source_id_to_db_id()
        self.additional_sign_source_id_to_db_id = self._build_additional_sign_source_id_to_db_id()
        self.signpost_source_id_to_db_id = self._build_signpost_source_id_to_db_id()

    @staticmethod
    def _build_mount_types_by_name() -> dict[str, MountType]:
        """Build a MountType lookup dict keyed by Finnish and English description.

        Returns:
            dict[str, MountType]: Mapping from description string to MountType instance.
        """
        result: dict[str, MountType] = {}
        for mt in MountType.objects.all():
            if mt.description_fi:
                result[mt.description_fi] = mt
            if mt.description:
                result[mt.description] = mt
        return result

    # ------------------------------------------------------------------
    # Mount handlers
    # ------------------------------------------------------------------

    def _create_mounts(self, summary: dict[str, Any]) -> None:
        """Create new MountReal records from CSV rows not yet in the DB.

        Rows whose source_id already exists in mount_source_id_to_db_id are skipped
        because they belong to the update phase. Rows with invalid geometry are logged
        as skips.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries are
                appended to summary["details"] and summary["mounts_created"] is
                incremented.
        """
        existing_source_ids: set[str] = set(self.mount_source_id_to_db_id.keys())
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("mounts_created", 0)
        details_before = len(summary.get("details", []))
        generator = self._get_mounts(
            skip_source_ids=existing_source_ids, summary=summary, phase_started_at=phase_started_at
        )
        if self.dry_run:
            created_count = 0
            for _ in generator:
                created_count += 1
        else:
            created = MountReal.objects.bulk_create(generator, batch_size=self.batch_size)
            created_count = len(created)
            # Write revert records after bulk_create — PKs are only available once
            # the batch has been committed. For creates the revert record only needs
            # the DB id (to know which row to delete on revert).
            for obj in created:
                self._write_revert_record(
                    {
                        "action": "create",
                        "object_type": "MountReal",
                        "db_id": str(obj.id),
                        "source_id": obj.source_id,
                    }
                )
        summary["mounts_created"] += created_count
        new_details = summary.get("details", [])[details_before:]
        skipped_count = sum(1 for e in new_details if e.get("level") == "skip")
        self._record_phase_result(summary, "mounts", "create", created=created_count, skipped=skipped_count)
        self._save_run_log(summary)

    def _get_mounts(
        self,
        skip_source_ids: set[str],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> Generator[MountReal, None, None]:
        """Yield MountReal instances built from CSV rows.

        Rows whose source_id is in skip_source_ids are silently skipped.
        Rows with invalid geometry are recorded as skip entries in summary["details"].

        Args:
            skip_source_ids (set[str]): Source IDs to exclude (already exist in DB,
                i.e. keys of mount_source_id_to_db_id).
            summary (dict[str, Any]): Mutable summary dict for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp of phase start, used as created_at.

        Yields:
            MountReal: Unsaved MountReal instance ready for bulk_create.
        """
        details: list[dict] = summary.setdefault("details", [])
        processed: list[str] = summary.setdefault("processed_mount_source_ids", [])
        # NOTE: source_ids are appended here (optimistically, before the DB write
        # succeeds) purely as an in-memory accumulator.  _save_run_log() is only
        # called after bulk_create() returns without error, so this list is never
        # persisted if a batch fails.  On re-run the union of *saved* run log rows
        # is used, so stale in-memory entries from a failed run are harmless.

        for source_id, row in self.mounts_by_id.items():
            if source_id in skip_source_ids:
                continue

            try:
                location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append({"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates: {exc}"})
                continue

            if not geometry_is_legit(location):
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid location: {location.ewkt}"}
                )
                continue

            raw_location_specifier = row.get(CSVHeadersV2.location_specifier, "")
            location_specifier = MountLocationSpecifier(int(raw_location_specifier)) if raw_location_specifier else None
            mount_type_name = row.get(CSVHeadersV2.mount_type, "")
            mount_type = self.mount_types_by_name.get(mount_type_name)

            processed.append(source_id)
            yield MountReal(
                source_id=source_id,
                source_name="StreetScan2025",
                location=location,
                owner=self.default_owner,
                installation_status=InstallationStatus.IN_USE,
                location_specifier=location_specifier,
                mount_type=mount_type,
                scanned_at=self._get_scanned_at(row.get(CSVHeadersV2.mount_scanned_at)),
                attachment_url=row.get(CSVHeadersV2.attachment_url, ""),
                created_by=self.user,
                created_at=phase_started_at,
            )

    @staticmethod
    def _get_scanned_at(date_str: str | None) -> datetime.datetime | None:
        """Parse the scanned_at timestamp from a CSV row value.

        Both mount and sign CSVs use the format ``2025/08/27 08:17:40+00``
        (slash-separated date, space separator, truncated timezone offset).
        Appending ``"00"`` before parsing corrects the truncated ``+00`` marker
        to a valid ``+0000`` offset.

        Args:
            date_str (str | None): Raw timestamp string from CSV, or None.

        Returns:
            datetime.datetime | None: Parsed UTC-aware datetime, or None if unparseable.
        """
        if not date_str:
            return None
        try:
            return datetime.datetime.strptime(date_str.strip() + "00", "%Y/%m/%d %H:%M:%S%z")
        except ValueError:
            return None

    def _save_run_log(self, summary: dict[str, Any]) -> None:
        """Persist the current run log state to the database.

        Called at the end of each phase so that progress is durable even if a
        later phase fails.

        Args:
            summary (dict[str, Any]): Current summary / run log dict.
        """
        if self.run_log is None:
            return
        self._apply_summary_to_run_log(self.run_log, summary)
        self.run_log.save()

    def _create_run_log(self) -> StreetScanImportRun:
        """Create and persist the initial StreetScanImportRun row for this run.

        Returns:
            StreetScanImportRun: The newly created (saved) run log instance.
        """
        run_log = StreetScanImportRun.objects.create(
            dry_run=self.dry_run,
            mount_file=self.mount_file,
            sign_file=self.sign_file,
            phase_durations={"preprocessing": {"total": round(self._preprocessing_duration_s, 2)}},
        )
        logger.debug("Created StreetScanImportRun pk=%s", run_log.pk)
        return run_log

    @staticmethod
    def _apply_summary_to_run_log(run_log: StreetScanImportRun, summary: dict[str, Any]) -> None:
        """Copy count and detail fields from summary into the run log model instance.

        Does not call save() — the caller is responsible for persisting.

        Args:
            run_log (StreetScanImportRun): Run log model instance to update.
            summary (dict[str, Any]): Current summary dict from the importer.
        """
        for field in (
            "mounts_created",
            "mounts_updated",
            "signs_created",
            "signs_updated",
            "signs_deactivated",
            "signposts_created",
            "signposts_updated",
            "signposts_deactivated",
            "additional_signs_created",
            "additional_signs_updated",
            "additional_signs_deactivated",
            "processed_mount_source_ids",
            "processed_sign_source_ids",
            "processed_signpost_source_ids",
            "processed_additional_sign_source_ids",
        ):
            if field in summary:
                setattr(run_log, field, summary[field])

        details: list[dict] = summary.get("details", [])
        run_log.details = details
        run_log.skipped_count = sum(1 for e in details if e.get("level") == "skip")
        run_log.warning_count = sum(1 for e in details if e.get("level") == "warning")
        run_log.error_count = sum(1 for e in details if e.get("level") == "error")

        # Extract phase durations from phase_results into the dedicated field,
        # preserving the 'preprocessing' key written at run_log creation.
        phase_durations: dict[str, dict[str, float]] = dict(run_log.phase_durations or {})
        for obj_type, phases in summary.get("phase_results", {}).items():
            phase_durations[obj_type] = {
                phase: counts.get("duration_s", 0.0) for phase, counts in phases.items() if "duration_s" in counts
            }
        run_log.phase_durations = phase_durations

    def _finalise_run_log(self, summary: dict[str, Any]) -> None:
        """Perform the final run log save and attach the revert file if applicable.

        For live runs, the temporary revert file is uploaded as a
        StreetScanImportRevertFile and then removed from the local filesystem.
        Dry runs skip the revert file creation entirely.

        Args:
            summary (dict[str, Any]): Final summary dict from the importer.
        """
        if self.run_log is None:
            return
        self._apply_summary_to_run_log(self.run_log, summary)
        self.run_log.completed_at = datetime.datetime.now(tz=datetime.timezone.utc)
        self.run_log.save()

        if not self.dry_run:
            self._attach_revert_file()

    def _attach_revert_file(self) -> None:
        """Upload the temporary revert file as a StreetScanImportRevertFile and clean up.

        Does nothing if no revert records were written (empty file).
        The local temporary file is always deleted after this method returns.
        """
        logger.debug("_attach_revert_file: run_log=%s, _revert_tmp=%s", self.run_log, self._revert_tmp)
        if self.run_log is None or self._revert_tmp is None:
            logger.debug("_attach_revert_file: skipping — run_log or _revert_tmp is None")
            return
        tmp_path = self._revert_tmp.name
        logger.debug("_attach_revert_file: tmp_path=%s", tmp_path)
        try:
            # Close the write handle before reading. Without this the file is still
            # open for writing; some storage backends (Azure Blob Storage in particular)
            # receive an empty or incomplete stream and raise BlobNotFound on verify.
            logger.debug("_attach_revert_file: closing write handle")
            self._revert_tmp.close()
            self._revert_tmp = None

            file_size = os.path.getsize(tmp_path)
            logger.debug("_attach_revert_file: file size after close = %d bytes", file_size)
            if file_size == 0:
                logger.debug("Revert file is empty — skipping attachment for run pk=%s", self.run_log.pk)
                return
            filename = f"revert_{self.run_log.started_at:%Y%m%d_%H%M%S}_{self.run_log.pk}.jsonl"
            logger.debug("_attach_revert_file: saving as '%s'", filename)
            revert_record = StreetScanImportRevertFile(import_run=self.run_log, is_public=False)
            with open(tmp_path, "rb") as fh:
                logger.debug("_attach_revert_file: opened tmp for reading, calling file.save()")
                revert_record.file.save(filename, File(fh), save=True)
            logger.debug(
                "_attach_revert_file: saved — storage name=%s, pk=%s",
                revert_record.file.name,
                revert_record.pk,
            )
        finally:
            try:
                os.unlink(tmp_path)
                logger.debug("_attach_revert_file: deleted tmp file %s", tmp_path)
            except OSError as exc:
                logger.warning("Could not delete temporary revert file %s: %s", tmp_path, exc)
            self._revert_tmp = None

    def _write_revert_record(self, record: dict[str, Any]) -> None:
        """Append a single revert record to the temporary revert file.

        Opens the temp file on the first call (lazy init). Each record is
        written as one JSON line (JSONL format) and flushed immediately to disk,
        guaranteeing durability before the corresponding DB write occurs.
        Memory overhead is O(1) regardless of the total number of records.

        Must be called *before* the corresponding DB write.

        Args:
            record (dict[str, Any]): Revert record dict with at minimum
                ``action``, ``object_type``, ``db_id``, and ``source_id`` keys.
        """
        if self.dry_run:
            return
        if self._revert_tmp is None:
            self._revert_tmp = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".jsonl",
                delete=False,
                encoding="utf-8",
            )
            logger.debug("_write_revert_record: opened tmp file %s", self._revert_tmp.name)
        self._revert_tmp.write(json.dumps(record, default=str) + "\n")
        self._revert_tmp.flush()
        logger.debug(
            "_write_revert_record: wrote action=%s object_type=%s source_id=%s to %s",
            record.get("action"),
            record.get("object_type"),
            record.get("source_id"),
            self._revert_tmp.name,
        )

    @staticmethod
    def _record_phase_result(
        summary: dict[str, Any],
        object_type: str,
        phase: str,
        **counts: int,
    ) -> None:
        """Record per-phase per-object-type result counts into summary["phase_results"].

        Args:
            summary (dict[str, Any]): Mutable summary dict.
            object_type (str): One of VALID_OBJECT_TYPES.
            phase (str): One of VALID_PHASES.
            **counts (int): Arbitrary named counters (e.g. created=5, skipped=2).
        """
        summary.setdefault("phase_results", {}).setdefault(object_type, {})[phase] = dict(counts)

    def _get_mounts_to_update(
        self,
        update_source_ids: list[str],
        db_id_map: dict[str, int],
        existing: dict[int, MountReal],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> Generator[MountReal, None, None]:
        """Yield MountReal instances that need to be updated.

        Applies geometry validation and (unless ``force_update`` is True) field
        comparison to determine whether each row requires a DB write. Revert
        records are written before each yield so they are always durable.
        ``updated_by`` and ``updated_at`` are always set and are intentionally
        excluded from the changed comparison so they do not trigger spurious updates.

        Args:
            update_source_ids (list[str]): Ordered list of source IDs to consider.
            db_id_map (dict[str, int]): Mapping from source_id to DB primary key.
            existing (dict[int, MountReal]): Currently persisted MountReal instances
                keyed by DB primary key.
            summary (dict[str, Any]): Mutable summary dict; skips are appended to

        Yields:
            MountReal: Mutated (unsaved) MountReal instance ready for bulk_update.
        """
        skipped: list[int] = summary.setdefault("_skipped_mount_update_count", [0])

        for source_id in update_source_ids:
            row = self.mounts_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped[0] += 1
                continue

            try:
                new_location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                summary.setdefault("details", []).append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates on update: {exc}"}
                )
                skipped[0] += 1
                continue

            if not geometry_is_legit(new_location):
                summary.setdefault("details", []).append(
                    {
                        "level": "skip",
                        "source_id": source_id,
                        "reason": f"Invalid location on update: {new_location.ewkt}",
                    }
                )
                skipped[0] += 1
                continue

            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            new_location_specifier = MountLocationSpecifier(int(raw_ls)) if raw_ls else None
            new_mount_type = self.mount_types_by_name.get(row.get(CSVHeadersV2.mount_type, ""))
            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.mount_scanned_at))
            new_attachment_url = row.get(CSVHeadersV2.attachment_url, "")
            new_source_name = "StreetScan2025"

            # When force_update is True the field comparison is bypassed entirely.
            changed = (
                self.force_update
                or obj.source_name != new_source_name
                or obj.scanned_at != new_scanned_at
                or obj.location != new_location
                or obj.location_specifier != new_location_specifier
                or obj.mount_type_id != (new_mount_type.pk if new_mount_type else None)
                or obj.attachment_url != new_attachment_url
            )
            if not changed:
                skipped[0] += 1
                continue

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "update",
                        "object_type": "MountReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "old": {
                            "source_name": obj.source_name,
                            "location": obj.location.ewkt if obj.location else None,
                            "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
                            "mount_type_id": obj.mount_type_id,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "attachment_url": obj.attachment_url,
                        },
                    }
                )

            obj.source_name = new_source_name
            obj.location = new_location
            obj.location_specifier = new_location_specifier
            obj.mount_type = new_mount_type
            obj.scanned_at = new_scanned_at
            obj.attachment_url = new_attachment_url
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            yield obj

    def _update_mounts(self, summary: dict[str, Any]) -> None:
        """Update existing MountReal records from CSV rows whose source_id is already in the DB.

        Fetches current DB state, computes new field values from CSV, and bulk-updates
        only the records where at least one field has changed. When ``force_update`` is
        True the field comparison is bypassed and all records are updated unconditionally.
        A revert record capturing the previous field values is written before each update
        so the run can be rolled back. Records are consumed from a generator and written
        in batches to keep memory usage O(batch_size).

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["mounts_updated"] and phase results are appended.
        """
        update_source_ids = [s for s in self.mounts_by_id if s in self.mount_source_id_to_db_id]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("mounts_updated", 0)
        if not update_source_ids:
            self._record_phase_result(summary, "mounts", "update", updated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.mount_source_id_to_db_id[s] for s in update_source_ids}
        existing: dict[int, MountReal] = {obj.pk: obj for obj in MountReal.objects.filter(pk__in=db_id_map.values())}

        update_fields = [
            "source_name",
            "location",
            "location_specifier",
            "mount_type",
            "scanned_at",
            "attachment_url",
            "updated_by",
            "updated_at",
        ]
        summary["_skipped_mount_update_count"] = [0]
        generator = self._get_mounts_to_update(update_source_ids, db_id_map, existing, summary, phase_started_at)

        # bulk_update does not accept a generator directly — unlike bulk_create which
        # handles generators natively with its batch_size parameter, bulk_update
        # internally slices the iterable (objs[i:i+batch_size]) which requires a
        # sequence supporting len() and slicing.  We therefore drain the generator
        # manually in fixed-size batches to keep memory consumption at O(batch_size).
        updated_count = 0
        batch: list[MountReal] = []
        for obj in generator:
            batch.append(obj)
            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    MountReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
                updated_count += len(batch)
                batch = []
        if batch:
            if not self.dry_run:
                MountReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
            updated_count += len(batch)

        skipped_count: int = summary.pop("_skipped_mount_update_count")[0]
        summary["mounts_updated"] += updated_count
        logger.info(
            "_update_mounts: updated=%d skipped=%d (of %d candidates)",
            updated_count,
            skipped_count,
            len(update_source_ids),
        )
        self._record_phase_result(summary, "mounts", "update", updated=updated_count, skipped=skipped_count)
        self._save_run_log(summary)

    # ------------------------------------------------------------------
    # Traffic sign field-cast helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_sign_height(height_str: str | None) -> int | None:
        """Convert height from metres (CSV) to centimetres (DB integer).

        Args:
            height_str (str | None): Raw height string from CSV, or None.

        Returns:
            int | None: Height in centimetres, or None if unparseable.
        """
        if not height_str:
            return None
        try:
            return int(float(height_str) * 100)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_sign_direction(direction_str: str | None) -> int | None:
        """Parse azimuth direction from CSV as integer degrees.

        Args:
            direction_str (str | None): Raw direction string from CSV, or None.

        Returns:
            int | None: Direction in degrees, or None if unparseable.
        """
        if not direction_str:
            return None
        try:
            return int(float(direction_str))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_sign_condition(condition_str: str | None) -> Condition | None:
        """Parse condition from CSV as Condition enum.

        Args:
            condition_str (str | None): Raw condition string from CSV, or None.

        Returns:
            Condition | None: Parsed Condition enum value, or None if unparseable.
        """
        if not condition_str:
            return None
        try:
            return Condition(int(condition_str))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_sign_value(number_code_str: str | None) -> Decimal | None:
        """Extract the leading numeric value from number_code field as Decimal.

        Args:
            number_code_str (str | None): Raw number_code string from CSV, or None.

        Returns:
            Decimal | None: Extracted value, or None if no numeric prefix found.
        """
        if not number_code_str:
            return None
        match = NUMBER_CODE_PATTERN.match(number_code_str.strip())
        if not match:
            return None
        try:
            return Decimal(match.group(1))
        except Exception:
            return None

    def _load_required_owners(self) -> tuple[Owner, Owner]:
        """Fetch the two owner records required by the importer.

        Called once at the start of ``__init__`` before any CSV or DB work so
        that a missing owner raises immediately without wasting time.

        Returns:
            tuple[Owner, Owner]: ``(default_owner, private_owner)`` — the
                Helsingin kaupunki and Yksityinen owner instances.

        Raises:
            RuntimeError: If either required owner is absent from the database.
        """
        try:
            default_owner = Owner.objects.get(name_fi="Helsingin kaupunki")
        except Owner.DoesNotExist:
            raise RuntimeError(
                "Required Owner 'Helsingin kaupunki' not found in the database. " "Cannot proceed with import."
            )
        try:
            private_owner = Owner.objects.get(name_fi="Yksityinen")
        except Owner.DoesNotExist:
            raise RuntimeError("Required Owner 'Yksityinen' not found in the database. " "Cannot proceed with import.")
        return default_owner, private_owner

    def _resolve_sign_owner(self, code: str, number_code_str: str) -> Owner:
        """Resolve the owner for a traffic sign row.

        Speed-limit signs with code ``363`` and a value of 5, 10, or 15 are
        owned by the private owner (Yksityinen); all other signs use the
        default city owner.

        Args:
            code (str): Device type code from the CSV row.
            number_code_str (str): Raw number_code value from the CSV row.

        Returns:
            Owner: The resolved owner for this sign.
        """
        _private_speed_values = {"5", "10", "15"}
        if code == "363" and number_code_str.strip() in _private_speed_values:
            return self.private_owner
        return self.default_owner

    # ------------------------------------------------------------------
    # Traffic sign handlers
    # ------------------------------------------------------------------

    def _create_signs(self, summary: dict[str, Any]) -> None:
        """Create new TrafficSignReal records from CSV rows not yet in the DB.

        Rows with ``status == "Removed"``, already present in the DB, with
        invalid geometry, or whose device type code is not found are skipped.
        Rows referencing an unknown mount or carrying a parent_sign_id value
        (which traffic signs do not support) are imported with a warning entry.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries are
                appended to summary["details"] and summary["signs_created"] is
                incremented.
        """
        existing_source_ids: set[str] = set(self.sign_source_id_to_db_id.keys())
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signs_created", 0)
        details_before = len(summary.get("details", []))
        generator = self._get_signs_to_create(
            existing_source_ids=existing_source_ids,
            summary=summary,
            phase_started_at=phase_started_at,
        )
        if self.dry_run:
            created_count = 0
            for _ in generator:
                created_count += 1
        else:
            created = TrafficSignReal.objects.bulk_create(generator, batch_size=self.batch_size)
            created_count = len(created)
            # Write revert records after bulk_create — PKs are only available once
            # the batch has been committed. For creates the revert record only needs
            # the DB id (to know which row to delete on revert).
            for obj in created:
                self._write_revert_record(
                    {
                        "action": "create",
                        "object_type": "TrafficSignReal",
                        "db_id": str(obj.id),
                        "source_id": obj.source_id,
                    }
                )
        summary["signs_created"] += created_count
        new_details = summary.get("details", [])[details_before:]
        skipped_count = sum(1 for e in new_details if e.get("level") == "skip")
        warning_count = sum(1 for e in new_details if e.get("level") == "warning")
        self._record_phase_result(
            summary, "signs", "create", created=created_count, skipped=skipped_count, warnings=warning_count
        )
        self._save_run_log(summary)

    def _get_signs_to_create(  # noqa: C901
        self,
        existing_source_ids: set[str],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> Generator[TrafficSignReal, None, None]:
        """Yield TrafficSignReal instances built from new CSV rows.

        Rows already in the DB, marked Removed, with invalid geometry, or whose
        device type code is not found are skipped with a details entry.
        Rows with an unresolved mount or a parent_sign_id value are imported with
        a warning details entry.

        Args:
            existing_source_ids (set[str]): Source IDs already present in the DB.
            summary (dict[str, Any]): Mutable summary dict for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp of phase start, used as created_at.

        Yields:
            TrafficSignReal: Unsaved TrafficSignReal instance ready for bulk_create.
        """

        details: list[dict] = summary.setdefault("details", [])
        processed: list[str] = summary.setdefault("processed_sign_source_ids", [])

        for source_id, row in self.signs_by_id.items():
            if source_id in existing_source_ids:
                continue
            if row.get(CSVHeadersV2.status) == "Removed":
                continue

            try:
                location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append({"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates: {exc}"})
                continue

            if not geometry_is_legit(location):
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid location: {location.ewkt}"}
                )
                continue

            code = row.get(CSVHeadersV2.code, "")
            device_type_id = self.code_to_device_type_id.get(code)
            if device_type_id is None:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"}
                )
                continue

            mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
            mount_real_id = None
            if mount_csv_id:
                mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
                if mount_real_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                        }
                    )

            parent_sign_id = row.get(CSVHeadersV2.parent_sign_id, "")
            if parent_sign_id:
                details.append(
                    {
                        "level": "warning",
                        "source_id": source_id,
                        "reason": f"Traffic sign has parent_sign_id={parent_sign_id!r}; ignored (no parent FK)",
                    }
                )

            number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
            value = self._get_sign_value(number_code_str)
            owner = self._resolve_sign_owner(code, number_code_str)

            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
            sign_mount_type_name = row.get(CSVHeadersV2.sign_mount_type, "")
            mount_type = self.mount_types_by_name.get(sign_mount_type_name)

            processed.append(source_id)
            yield TrafficSignReal(
                source_id=source_id,
                source_name="StreetScan2025",
                location=location,
                device_type_id=device_type_id,
                owner=owner,
                installation_status=InstallationStatus.IN_USE,
                lifecycle=Lifecycle.ACTIVE,
                mount_real_id=mount_real_id,
                mount_type=mount_type,
                direction=self._get_sign_direction(row.get(CSVHeadersV2.direction)),
                height=self._get_sign_height(row.get(CSVHeadersV2.height)),
                condition=self._get_sign_condition(row.get(CSVHeadersV2.condition)),
                location_specifier=location_specifier,
                value=value,
                txt=row.get(CSVHeadersV2.txt, "") or None,
                scanned_at=self._get_scanned_at(row.get(CSVHeadersV2.scanned_at)),
                attachment_url=row.get(CSVHeadersV2.attachment_url, ""),
                created_by=self.user,
                created_at=phase_started_at,
            )

    def _get_signs_to_update(  # noqa: C901
        self,
        update_source_ids: list[str],
        db_id_map: dict[str, int],
        existing: dict[int, TrafficSignReal],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> Generator[TrafficSignReal, None, None]:
        """Yield TrafficSignReal instances that need to be updated.

        Applies geometry validation and (unless ``force_update`` is True) field
        comparison to determine whether each row requires a DB write. Revert
        records are written before each yield so they are always durable.
        ``updated_by`` and ``updated_at`` are always set and are intentionally
        excluded from the changed comparison so they do not trigger spurious updates.

        Args:
            update_source_ids (list[str]): Ordered list of source IDs to consider.
            db_id_map (dict[str, int]): Mapping from source_id to DB primary key.
            existing (dict[int, TrafficSignReal]): Currently persisted instances
                keyed by DB primary key.
            default_owner (Owner): City of Helsinki owner instance.
            private_owner (Owner): Private owner instance.
            summary (dict[str, Any]): Mutable summary dict; skips/warnings are
                appended to summary["details"].
            phase_started_at (datetime.datetime): Timestamp of phase start, used as updated_at.

        Yields:
            TrafficSignReal: Mutated (unsaved) instance ready for bulk_update.
        """
        skipped: list[int] = summary.setdefault("_skipped_sign_update_count", [0])
        details: list[dict] = summary.setdefault("details", [])

        for source_id in update_source_ids:
            row = self.signs_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped[0] += 1
                continue

            try:
                new_location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates on update: {exc}"}
                )
                skipped[0] += 1
                continue

            if not geometry_is_legit(new_location):
                details.append(
                    {
                        "level": "skip",
                        "source_id": source_id,
                        "reason": f"Invalid location on update: {new_location.ewkt}",
                    }
                )
                skipped[0] += 1
                continue

            code = row.get(CSVHeadersV2.code, "")
            device_type_id = self.code_to_device_type_id.get(code)
            if device_type_id is None:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"}
                )
                skipped[0] += 1
                continue

            mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
            mount_real_id = None
            if mount_csv_id:
                mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
                if mount_real_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                        }
                    )

            parent_sign_id = row.get(CSVHeadersV2.parent_sign_id, "")
            if parent_sign_id:
                details.append(
                    {
                        "level": "warning",
                        "source_id": source_id,
                        "reason": f"Traffic sign has parent_sign_id={parent_sign_id!r}; ignored (no parent FK)",
                    }
                )

            number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
            new_value = self._get_sign_value(number_code_str)
            new_owner = self._resolve_sign_owner(code, number_code_str)
            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            new_location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
            sign_mount_type_name = row.get(CSVHeadersV2.sign_mount_type, "")
            new_mount_type = self.mount_types_by_name.get(sign_mount_type_name)
            new_direction = self._get_sign_direction(row.get(CSVHeadersV2.direction))
            new_height = self._get_sign_height(row.get(CSVHeadersV2.height))
            new_condition = self._get_sign_condition(row.get(CSVHeadersV2.condition))
            new_txt = row.get(CSVHeadersV2.txt, "") or None
            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at))
            new_attachment_url = row.get(CSVHeadersV2.attachment_url, "")
            new_source_name = "StreetScan2025"

            # When force_update is True the field comparison is bypassed entirely.
            changed = (
                self.force_update
                or obj.source_name != new_source_name
                or obj.location != new_location
                or obj.device_type_id != device_type_id
                or obj.mount_real_id != mount_real_id
                or obj.mount_type_id != (new_mount_type.pk if new_mount_type else None)
                or obj.direction != new_direction
                or obj.height != new_height
                or obj.condition != new_condition
                or obj.location_specifier != new_location_specifier
                or obj.value != new_value
                or obj.txt != new_txt
                or obj.scanned_at != new_scanned_at
                or obj.attachment_url != new_attachment_url
            )
            if not changed:
                skipped[0] += 1
                continue

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "update",
                        "object_type": "TrafficSignReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "old": {
                            "source_name": obj.source_name,
                            "location": obj.location.ewkt if obj.location else None,
                            "device_type_id": obj.device_type_id,
                            "mount_real_id": obj.mount_real_id,
                            "mount_type_id": obj.mount_type_id,
                            "direction": obj.direction,
                            "height": obj.height,
                            "condition": str(obj.condition) if obj.condition else None,
                            "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
                            "value": str(obj.value) if obj.value is not None else None,
                            "txt": obj.txt,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "attachment_url": obj.attachment_url,
                        },
                    }
                )

            obj.source_name = new_source_name
            obj.location = new_location
            obj.device_type_id = device_type_id
            obj.owner = new_owner
            obj.installation_status = InstallationStatus.IN_USE
            obj.lifecycle = Lifecycle.ACTIVE
            obj.mount_real_id = mount_real_id
            obj.mount_type = new_mount_type
            obj.direction = new_direction
            obj.height = new_height
            obj.condition = new_condition
            obj.location_specifier = new_location_specifier
            obj.value = new_value
            obj.txt = new_txt
            obj.scanned_at = new_scanned_at
            obj.attachment_url = new_attachment_url
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            yield obj

    def _update_signs(self, summary: dict[str, Any]) -> None:
        """Update existing TrafficSignReal records from CSV rows already in the DB.

        Fetches current DB state, computes new field values from CSV, and bulk-updates
        only the records where at least one field has changed. When ``force_update`` is
        True the field comparison is bypassed and all records are updated unconditionally.
        A revert record capturing the previous field values is written before each update
        so the run can be rolled back. Records are consumed from a generator and written
        in batches to keep memory usage O(batch_size).

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["signs_updated"] and phase results are appended.
        """
        update_source_ids = [
            s
            for s, row in self.signs_by_id.items()
            if s in self.sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signs_updated", 0)
        if not update_source_ids:
            self._record_phase_result(summary, "signs", "update", updated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.sign_source_id_to_db_id[s] for s in update_source_ids}
        existing: dict[int, TrafficSignReal] = {
            obj.pk: obj for obj in TrafficSignReal.objects.filter(pk__in=db_id_map.values())
        }

        update_fields = [
            "source_name",
            "location",
            "device_type",
            "owner",
            "installation_status",
            "lifecycle",
            "mount_real",
            "mount_type",
            "direction",
            "height",
            "condition",
            "location_specifier",
            "value",
            "txt",
            "scanned_at",
            "attachment_url",
            "updated_by",
            "updated_at",
        ]
        summary["_skipped_sign_update_count"] = [0]
        generator = self._get_signs_to_update(
            update_source_ids,
            db_id_map,
            existing,
            summary,
            phase_started_at,
        )

        # bulk_update does not accept a generator directly — unlike bulk_create which
        # handles generators natively with its batch_size parameter, bulk_update
        # internally slices the iterable (objs[i:i+batch_size]) which requires a
        # sequence supporting len() and slicing.  We therefore drain the generator
        # manually in fixed-size batches to keep memory consumption at O(batch_size).
        updated_count = 0
        warnings_count = 0
        details_before = len(summary.get("details", []))
        batch: list[TrafficSignReal] = []
        for obj in generator:
            batch.append(obj)
            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    TrafficSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
                updated_count += len(batch)
                batch = []
        if batch:
            if not self.dry_run:
                TrafficSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
            updated_count += len(batch)

        skipped_count: int = summary.pop("_skipped_sign_update_count")[0]
        new_details = summary.get("details", [])[details_before:]
        warnings_count = sum(1 for e in new_details if e.get("level") == "warning")
        summary["signs_updated"] += updated_count
        logger.info(
            "_update_signs: updated=%d skipped=%d warnings=%d (of %d candidates)",
            updated_count,
            skipped_count,
            warnings_count,
            len(update_source_ids),
        )
        self._record_phase_result(
            summary, "signs", "update", updated=updated_count, skipped=skipped_count, warnings=warnings_count
        )
        self._save_run_log(summary)

    def _deactivate_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate TrafficSignReal records marked as Removed in CSV.

        Deactivation updates exactly six fields on each matching record:
        ``lifecycle`` → ``Lifecycle.INACTIVE``,
        ``validity_period_end`` → date portion of the CSV ``scanned_at`` timestamp
        (falls back to today if the field is absent or unparseable),
        ``scanned_at`` → CSV timestamp, ``source_name`` → ``"StreetScan2025"``,
        ``updated_by`` → the configured user, ``updated_at`` → phase start time.
        No other fields are modified.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["signs_deactivated"] and phase results are
                appended.
        """
        deactivate_source_ids = [
            s
            for s, row in self.signs_by_id.items()
            if s in self.sign_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
        ]
        summary.setdefault("signs_deactivated", 0)
        if not deactivate_source_ids:
            self._record_phase_result(summary, "signs", "deactivate", deactivated=0)
            self._save_run_log(summary)
            return

        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        db_id_map: dict[str, int] = {s: self.sign_source_id_to_db_id[s] for s in deactivate_source_ids}
        existing: dict[int, TrafficSignReal] = {
            obj.pk: obj for obj in TrafficSignReal.objects.filter(pk__in=db_id_map.values())
        }

        deactivated_count = 0
        batch: list[TrafficSignReal] = []
        for source_id in deactivate_source_ids:
            row = self.signs_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                continue

            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at))
            validity_end = new_scanned_at.date() if new_scanned_at else None

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "deactivate",
                        "object_type": "TrafficSignReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "old": {
                            "lifecycle": obj.lifecycle,
                            "validity_period_end": str(obj.validity_period_end) if obj.validity_period_end else None,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "source_name": obj.source_name,
                        },
                    }
                )

            obj.lifecycle = Lifecycle.INACTIVE
            obj.validity_period_end = validity_end
            obj.scanned_at = new_scanned_at
            obj.source_name = "StreetScan2025"
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            batch.append(obj)

            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    TrafficSignReal.objects.bulk_update(
                        batch,
                        ["lifecycle", "validity_period_end", "scanned_at", "source_name", "updated_by", "updated_at"],
                        batch_size=self.batch_size,
                    )
                deactivated_count += len(batch)
                batch = []

        if batch:
            if not self.dry_run:
                TrafficSignReal.objects.bulk_update(
                    batch,
                    ["lifecycle", "validity_period_end", "scanned_at", "source_name", "updated_by", "updated_at"],
                    batch_size=self.batch_size,
                )
            deactivated_count += len(batch)

        summary["signs_deactivated"] += deactivated_count
        logger.info(
            "_deactivate_signs: deactivated=%d (of %d candidates)", deactivated_count, len(deactivate_source_ids)
        )
        self._record_phase_result(summary, "signs", "deactivate", deactivated=deactivated_count)
        self._save_run_log(summary)

    # ------------------------------------------------------------------
    # Signpost handlers
    # ------------------------------------------------------------------

    def _create_signposts(self, summary: dict[str, Any]) -> None:
        """Create new SignpostReal records using a two-pass strategy.

        Pass 1 inserts root signposts (no ``parent_sign_id``).  Pass 2 inserts
        child signposts whose parent was either already in the DB before this
        run or was created in pass 1.  Signposts whose parent is still not
        found after both passes are imported without a parent and a warning is
        recorded.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries
                are appended to summary["details"] and summary["signposts_created"]
                is incremented.
        """
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signposts_created", 0)
        details_before = len(summary.get("details", []))

        # In-run map: source_id → db pk for signposts created during pass 1.
        # Combined with the pre-existing signpost_source_id_to_db_id it gives
        # the full parent-resolution map available during pass 2.
        newly_created: dict[str, int] = {}

        existing_source_ids: set[str] = set(self.signpost_source_id_to_db_id.keys())
        candidate_source_ids = [
            s
            for s, row in self.signposts_by_id.items()
            if s not in existing_source_ids and row.get(CSVHeadersV2.status) != "Removed"
        ]
        # Partition into roots (no parent) and children (have parent_sign_id).
        root_ids = [s for s in candidate_source_ids if not self.signposts_by_id[s].get(CSVHeadersV2.parent_sign_id, "")]
        child_ids = [s for s in candidate_source_ids if s not in root_ids]

        created_count = self._run_signpost_pass(
            source_ids=root_ids,
            parent_map={**self.signpost_source_id_to_db_id, **newly_created},
            newly_created=newly_created,
            summary=summary,
            phase_started_at=phase_started_at,
        )
        # Refresh the combined map with pass-1 results before pass 2.
        combined_parent_map = {**self.signpost_source_id_to_db_id, **newly_created}
        created_count += self._run_signpost_pass(
            source_ids=child_ids,
            parent_map=combined_parent_map,
            newly_created=newly_created,
            summary=summary,
            phase_started_at=phase_started_at,
        )

        summary["signposts_created"] += created_count
        new_details = summary.get("details", [])[details_before:]
        skipped_count = sum(1 for e in new_details if e.get("level") == "skip")
        warning_count = sum(1 for e in new_details if e.get("level") == "warning")
        self._record_phase_result(
            summary,
            "signposts",
            "create",
            created=created_count,
            skipped=skipped_count,
            warnings=warning_count,
        )
        self._save_run_log(summary)

    def _run_signpost_pass(  # noqa: C901
        self,
        source_ids: list[str],
        parent_map: dict[str, int],
        newly_created: dict[str, int],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> int:
        """Insert one batch of signpost rows (either roots or children).

        Args:
            source_ids (list[str]): Ordered list of source IDs for this pass.
            parent_map (dict[str, int]): Combined source_id → DB PK map covering
                pre-existing and pass-1-created signposts.
            newly_created (dict[str, int]): Mutable map updated with PKs created
                in this pass so subsequent passes can resolve them.
            summary (dict[str, Any]): Mutable summary dict for details entries.
            phase_started_at (datetime.datetime): Timestamp used as created_at.

        Returns:
            int: Number of signposts created in this pass.
        """

        details: list[dict] = summary.setdefault("details", [])
        processed: list[str] = summary.setdefault("processed_signpost_source_ids", [])

        objects_to_create: list[SignpostReal] = []

        for source_id in source_ids:
            row = self.signposts_by_id[source_id]

            try:
                location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append({"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates: {exc}"})
                continue

            if not geometry_is_legit(location):
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid location: {location.ewkt}"}
                )
                continue

            code = row.get(CSVHeadersV2.code, "")
            device_type_id = self.code_to_device_type_id.get(code)
            if device_type_id is None:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"}
                )
                continue

            # Mount resolution — warn but still import without mount.
            mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
            mount_real_id = None
            if mount_csv_id:
                mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
                if mount_real_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                        }
                    )

            # Parent signpost resolution — warn but still import without parent.
            parent_csv_id = row.get(CSVHeadersV2.parent_sign_id, "")
            parent_id = None
            if parent_csv_id:
                parent_id = parent_map.get(parent_csv_id)
                if parent_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Parent signpost not found for parent CSV id: {parent_csv_id}",
                        }
                    )

            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
            sign_mount_type_name = row.get(CSVHeadersV2.sign_mount_type, "")
            mount_type = self.mount_types_by_name.get(sign_mount_type_name)
            number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
            value = self._get_sign_value(number_code_str)

            processed.append(source_id)
            objects_to_create.append(
                SignpostReal(
                    source_id=source_id,
                    source_name="StreetScan2025",
                    location=location,
                    device_type_id=device_type_id,
                    owner=self.default_owner,
                    installation_status=InstallationStatus.IN_USE,
                    lifecycle=Lifecycle.ACTIVE,
                    parent_id=parent_id,
                    mount_real_id=mount_real_id,
                    mount_type=mount_type,
                    direction=self._get_sign_direction(row.get(CSVHeadersV2.direction)),
                    height=self._get_sign_height(row.get(CSVHeadersV2.height)),
                    condition=self._get_sign_condition(row.get(CSVHeadersV2.condition)),
                    location_specifier=location_specifier,
                    value=value,
                    txt=row.get(CSVHeadersV2.txt, "") or None,
                    scanned_at=self._get_scanned_at(row.get(CSVHeadersV2.scanned_at)),
                    attachment_url=row.get(CSVHeadersV2.attachment_url, ""),
                    created_by=self.user,
                    created_at=phase_started_at,
                )
            )

        if not objects_to_create:
            return 0

        if self.dry_run:
            return len(objects_to_create)

        created = SignpostReal.objects.bulk_create(objects_to_create, batch_size=self.batch_size)
        for obj in created:
            newly_created[obj.source_id] = obj.pk
            self._write_revert_record(
                {
                    "action": "create",
                    "object_type": "SignpostReal",
                    "db_id": str(obj.id),
                    "source_id": obj.source_id,
                }
            )
        return len(created)

    def _update_signposts(self, summary: dict[str, Any]) -> None:
        """Update existing SignpostReal records from non-Removed CSV rows.

        Rows whose source_id is not already in the DB are ignored (they belong
        to the create phase).  Removed rows are also ignored here.  Only rows
        whose field values differ from the DB (or when ``force_update`` is True)
        are written.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["signposts_updated"] and phase results are
                appended.
        """
        update_source_ids = [
            s
            for s, row in self.signposts_by_id.items()
            if s in self.signpost_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signposts_updated", 0)
        if not update_source_ids:
            self._record_phase_result(summary, "signposts", "update", updated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.signpost_source_id_to_db_id[s] for s in update_source_ids}
        existing: dict[int, Any] = {obj.pk: obj for obj in SignpostReal.objects.filter(pk__in=db_id_map.values())}
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)

        update_fields = [
            "source_name",
            "location",
            "device_type_id",
            "owner",
            "mount_real_id",
            "mount_type",
            "direction",
            "height",
            "condition",
            "location_specifier",
            "value",
            "txt",
            "scanned_at",
            "attachment_url",
            "updated_by",
            "updated_at",
        ]
        updated_count = 0
        skipped_count = 0
        batch: list[Any] = []

        for source_id in update_source_ids:
            row = self.signposts_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped_count += 1
                continue

            fields = self._resolve_signpost_update_fields(row, source_id, details)
            if fields is None:
                skipped_count += 1
                continue

            new_location, device_type_id, new_mount_real_id, new_mount_type = (
                fields["location"],
                fields["device_type_id"],
                fields["mount_real_id"],
                fields["mount_type"],
            )
            new_location_specifier = fields["location_specifier"]
            new_value, new_height, new_direction = fields["value"], fields["height"], fields["direction"]
            new_condition, new_scanned_at = fields["condition"], fields["scanned_at"]
            new_attachment_url, new_txt = fields["attachment_url"], fields["txt"]
            new_source_name = "StreetScan2025"

            if not self._signpost_fields_changed(
                obj,
                new_source_name,
                new_location,
                device_type_id,
                new_mount_real_id,
                new_mount_type,
                new_direction,
                new_height,
                new_condition,
                new_location_specifier,
                new_value,
                new_txt,
                new_scanned_at,
                new_attachment_url,
            ):
                skipped_count += 1
                continue

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "update",
                        "object_type": "SignpostReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "old": {
                            "source_name": obj.source_name,
                            "location": obj.location.ewkt if obj.location else None,
                            "device_type_id": obj.device_type_id,
                            "mount_real_id": obj.mount_real_id,
                            "direction": obj.direction,
                            "height": str(obj.height) if obj.height is not None else None,
                            "condition": obj.condition,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "attachment_url": obj.attachment_url,
                        },
                    }
                )

            obj.source_name = new_source_name
            obj.location = new_location
            obj.device_type_id = device_type_id
            obj.owner = self.default_owner
            obj.mount_real_id = new_mount_real_id
            obj.mount_type = new_mount_type
            obj.direction = new_direction
            obj.height = new_height
            obj.condition = new_condition
            obj.location_specifier = new_location_specifier
            obj.value = new_value
            obj.txt = new_txt
            obj.scanned_at = new_scanned_at
            obj.attachment_url = new_attachment_url
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            batch.append(obj)

            if len(batch) >= self.batch_size:
                self._flush_signpost_batch(batch, update_fields)
                updated_count += len(batch)
                batch = []

        self._flush_signpost_batch(batch, update_fields)
        updated_count += len(batch)

        skipped_count += len([e for e in summary.get("details", [])[details_before:] if e.get("level") == "skip"])
        summary["signposts_updated"] += updated_count
        logger.info(
            "_update_signposts: updated=%d skipped=%d (of %d candidates)",
            updated_count,
            skipped_count,
            len(update_source_ids),
        )
        self._record_phase_result(summary, "signposts", "update", updated=updated_count, skipped=skipped_count)
        self._save_run_log(summary)

    def _flush_signpost_batch(self, batch: list[Any], update_fields: list[str]) -> None:
        """Write a batch of SignpostReal objects to the DB unless in dry-run mode.

        Args:
            batch (list[Any]): Signpost instances to bulk-update.
            update_fields (list[str]): Field names to include in the bulk update.
        """
        if batch and not self.dry_run:
            SignpostReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)

    def _resolve_signpost_update_fields(self, row: dict, source_id: str, details: list[dict]) -> dict[str, Any] | None:
        """Resolve and validate all field values for a signpost update row.

        Validates geometry and device type code, resolves FK ids, and casts all
        field values. Returns ``None`` and appends a skip entry to ``details``
        when a hard validation error is encountered.

        Args:
            row (dict): Enriched CSV row for the signpost.
            source_id (str): Source identifier for logging.
            details (list[dict]): Mutable details list to append skip/warning entries.

        Returns:
            dict[str, Any] | None: Resolved field dict, or None if the row must be skipped.
        """
        try:
            new_location = self._georeferenced_point_from_csv_row(row)
        except (KeyError, ValueError) as exc:
            details.append({"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates on update: {exc}"})
            return None

        if not geometry_is_legit(new_location):
            details.append(
                {"level": "skip", "source_id": source_id, "reason": f"Invalid location on update: {new_location.ewkt}"}
            )
            return None

        code = row.get(CSVHeadersV2.code, "")
        device_type_id = self.code_to_device_type_id.get(code)
        if device_type_id is None:
            details.append({"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"})
            return None

        mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
        new_mount_real_id = None
        if mount_csv_id:
            new_mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
            if new_mount_real_id is None:
                details.append(
                    {
                        "level": "warning",
                        "source_id": source_id,
                        "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                    }
                )

        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        return {
            "location": new_location,
            "device_type_id": device_type_id,
            "mount_real_id": new_mount_real_id,
            "mount_type": self.mount_types_by_name.get(row.get(CSVHeadersV2.sign_mount_type, "")),
            "location_specifier": SignLocationSpecifier(int(raw_ls)) if raw_ls else None,
            "value": self._get_sign_value(row.get(CSVHeadersV2.number_code, "") or ""),
            "height": self._get_sign_height(row.get(CSVHeadersV2.height)),
            "direction": self._get_sign_direction(row.get(CSVHeadersV2.direction)),
            "condition": self._get_sign_condition(row.get(CSVHeadersV2.condition)),
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.scanned_at)),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
            "txt": row.get(CSVHeadersV2.txt, "") or None,
        }

    def _signpost_fields_changed(  # noqa: PLR0913
        self,
        obj: Any,
        new_source_name: str,
        new_location: Any,
        device_type_id: int,
        new_mount_real_id: int | None,
        new_mount_type: Any,
        new_direction: int | None,
        new_height: int | None,
        new_condition: Any,
        new_location_specifier: Any,
        new_value: Decimal | None,
        new_txt: str | None,
        new_scanned_at: Any,
        new_attachment_url: str,
    ) -> bool:
        """Return True if any signpost field differs from the stored DB values.

        Args:
            obj (Any): Existing SignpostReal DB instance.
            new_source_name (str): New source_name value.
            new_location (Any): New geometry point.
            device_type_id (int): New device type PK.
            new_mount_real_id (int | None): New mount FK.
            new_mount_type (Any): New MountType instance or None.
            new_direction (int | None): New direction value.
            new_height (int | None): New height value in cm.
            new_condition (Any): New condition enum value.
            new_location_specifier (Any): New location specifier enum value.
            new_value (Decimal | None): New sign value.
            new_txt (str | None): New text value.
            new_scanned_at (Any): New scanned_at datetime.
            new_attachment_url (str): New attachment URL.

        Returns:
            bool: True if any field has changed or force_update is set.
        """
        if self.force_update:
            return True
        return (
            obj.source_name != new_source_name
            or obj.location != new_location
            or obj.device_type_id != device_type_id
            or obj.mount_real_id != new_mount_real_id
            or obj.mount_type_id != (new_mount_type.pk if new_mount_type else None)
            or obj.direction != new_direction
            or obj.height != new_height
            or obj.condition != new_condition
            or obj.location_specifier != new_location_specifier
            or obj.value != new_value
            or obj.txt != new_txt
            or obj.scanned_at != new_scanned_at
            or obj.attachment_url != new_attachment_url
        )

    def _deactivate_signposts(self, summary: dict[str, Any]) -> None:
        """Deactivate SignpostReal records whose CSV status is ``Removed``.

        Deactivation sets ``lifecycle`` to ``Lifecycle.INACTIVE``,
        ``validity_period_end`` to the date portion of the CSV ``scanned_at``
        timestamp (falls back to today if absent or unparseable),
        ``scanned_at`` to the CSV timestamp, ``source_name`` to
        ``"StreetScan2025"``, and also updates ``updated_by`` and ``updated_at``.
        No other fields are modified.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["signposts_deactivated"] and phase results
                are appended.
        """

        deactivate_source_ids = [
            s
            for s, row in self.signposts_by_id.items()
            if s in self.signpost_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signposts_deactivated", 0)
        if not deactivate_source_ids:
            self._record_phase_result(summary, "signposts", "deactivate", deactivated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.signpost_source_id_to_db_id[s] for s in deactivate_source_ids}
        existing: dict[int, Any] = {obj.pk: obj for obj in SignpostReal.objects.filter(pk__in=db_id_map.values())}
        update_fields = ["lifecycle", "validity_period_end", "scanned_at", "source_name", "updated_by", "updated_at"]
        batch: list[Any] = []
        deactivated_count = 0

        for source_id in deactivate_source_ids:
            row = self.signposts_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                continue

            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at))
            validity_end = new_scanned_at.date() if new_scanned_at else None

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "deactivate",
                        "object_type": "SignpostReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "before": {
                            "lifecycle": obj.lifecycle,
                            "validity_period_end": str(obj.validity_period_end) if obj.validity_period_end else None,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "source_name": obj.source_name,
                        },
                    }
                )

            obj.lifecycle = Lifecycle.INACTIVE
            obj.validity_period_end = validity_end
            obj.scanned_at = new_scanned_at
            obj.source_name = "StreetScan2025"
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            batch.append(obj)

            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    SignpostReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
                deactivated_count += len(batch)
                batch = []

        if batch:
            if not self.dry_run:
                SignpostReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
            deactivated_count += len(batch)

        summary["signposts_deactivated"] += deactivated_count
        logger.info(
            "_deactivate_signposts: deactivated=%d (of %d candidates)", deactivated_count, len(deactivate_source_ids)
        )
        self._record_phase_result(summary, "signposts", "deactivate", deactivated=deactivated_count, skipped=0)
        self._save_run_log(summary)

    # ------------------------------------------------------------------
    # Additional sign handlers (skeleton)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Additional sign field helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_additional_sign_color(color_str: str | None) -> Color | None:
        """Parse the color field into a Color enum value.

        Args:
            color_str (str | None): Raw color string from CSV, or None.

        Returns:
            Color | None: Parsed Color enum value, or None if absent/invalid.
        """
        if not color_str:
            return None
        try:
            value = int(color_str)
            return Color(value) if value else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _build_additional_information(txt: str, number_code: str, internal_info: str | None) -> str:
        """Compose the additional_information field value from CSV fields.

        Format: ``"text:{txt}; numbercode:{number_code}"``
        With enrichment hint: ``"text:{txt}; numbercode:{number_code}; info:{internal_info}"``

        Args:
            txt (str): Raw teksti value from CSV.
            number_code (str): Raw numerokoodi value from CSV.
            internal_info (str | None): Preprocessed internal_additional_info hint, or None.

        Returns:
            str: Composed additional_information string.
        """
        base = f"text:{txt.strip()}; numbercode:{number_code.strip()}"
        hint = (internal_info or "").strip()
        return f"{base}; info:{hint}" if hint else base

    def _resolve_additional_sign_parent(
        self,
        parent_csv_id: str,
        source_id: str,
        details: list[dict],
    ) -> tuple[int | None, int | None]:
        """Resolve parent_sign_id to either a TrafficSignReal PK or a SignpostReal PK.

        Checks sign_source_id_to_db_id first, then signpost_source_id_to_db_id.
        Logs a warning if the id is non-blank but matches neither map.

        Args:
            parent_csv_id (str): CSV parent_sign_id value.
            source_id (str): Source ID of the additional sign being resolved (for warning logging).
            details (list[dict]): Mutable details list from summary.

        Returns:
            tuple[int | None, int | None]: (parent_id, signpost_real_id) — at most one is non-None.
        """
        if not parent_csv_id:
            return None, None

        traffic_sign_pk = self.sign_source_id_to_db_id.get(parent_csv_id)
        if traffic_sign_pk is not None:
            return traffic_sign_pk, None

        signpost_pk = self.signpost_source_id_to_db_id.get(parent_csv_id)
        if signpost_pk is not None:
            return None, signpost_pk

        details.append(
            {
                "level": "warning",
                "source_id": source_id,
                "reason": f"Parent sign not found in signs or signposts for parent CSV id: {parent_csv_id}",
            }
        )
        return None, None

    # ------------------------------------------------------------------
    # Additional sign phase handlers
    # ------------------------------------------------------------------

    def _create_additional_signs(self, summary: dict[str, Any]) -> None:  # noqa: C901
        """Create new AdditionalSignReal records from CSV rows not yet in the DB.

        Rows with ``status == "Removed"``, already present in the DB, with
        invalid geometry, unreadable text, or whose device type code is not found
        are skipped. An unresolved parent_sign_id is imported with a warning.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries
                are appended to summary["details"] and
                summary["additional_signs_created"] is incremented.
        """
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("additional_signs_created", 0)
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)
        processed: list[str] = summary.setdefault("processed_additional_sign_source_ids", [])

        existing_source_ids: set[str] = set(self.additional_sign_source_id_to_db_id.keys())
        objects_to_create: list[AdditionalSignReal] = []

        for source_id, row in self.additional_signs_by_id.items():
            if source_id in existing_source_ids or row.get(CSVHeadersV2.status) == "Removed":
                continue

            txt = row.get(CSVHeadersV2.txt, "") or ""
            if txt.strip().lower() == "unreadable":
                details.append({"level": "skip", "source_id": source_id, "reason": "text value is unreadable"})
                continue

            try:
                location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append({"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates: {exc}"})
                continue

            if not geometry_is_legit(location):
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid location: {location.ewkt}"}
                )
                continue

            code = row.get(CSVHeadersV2.code, "")
            device_type_id = self.code_to_device_type_id.get(code)
            if device_type_id is None:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"}
                )
                continue

            mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
            mount_real_id = None
            if mount_csv_id:
                mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
                if mount_real_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                        }
                    )

            parent_csv_id = row.get(CSVHeadersV2.parent_sign_id, "")
            parent_id, signpost_real_id = self._resolve_additional_sign_parent(parent_csv_id, source_id, details)

            number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
            sign_mount_type_name = row.get(CSVHeadersV2.sign_mount_type, "")
            mount_type = self.mount_types_by_name.get(sign_mount_type_name)
            internal_info = row.get("internal_additional_info")
            additional_information = self._build_additional_information(txt, number_code_str, internal_info)

            processed.append(source_id)
            objects_to_create.append(
                AdditionalSignReal(
                    source_id=source_id,
                    source_name="StreetScan2025",
                    location=location,
                    device_type_id=device_type_id,
                    owner=self.default_owner,
                    installation_status=InstallationStatus.IN_USE,
                    lifecycle=Lifecycle.ACTIVE,
                    missing_content=True,
                    parent_id=parent_id,
                    signpost_real_id=signpost_real_id,
                    mount_real_id=mount_real_id,
                    mount_type=mount_type,
                    direction=self._get_sign_direction(row.get(CSVHeadersV2.direction)),
                    height=self._get_sign_height(row.get(CSVHeadersV2.height)),
                    condition=self._get_sign_condition(row.get(CSVHeadersV2.condition)),
                    location_specifier=location_specifier,
                    color=self._get_additional_sign_color(row.get(CSVHeadersV2.color)),
                    additional_information=additional_information,
                    scanned_at=self._get_scanned_at(row.get(CSVHeadersV2.scanned_at)),
                    attachment_url=row.get(CSVHeadersV2.attachment_url, ""),
                    created_by=self.user,
                    created_at=phase_started_at,
                )
            )

        created_count = 0
        if objects_to_create:
            if self.dry_run:
                created_count = len(objects_to_create)
            else:
                created = AdditionalSignReal.objects.bulk_create(objects_to_create, batch_size=self.batch_size)
                created_count = len(created)
                for obj in created:
                    self._write_revert_record(
                        {
                            "action": "create",
                            "object_type": "AdditionalSignReal",
                            "db_id": str(obj.id),
                            "source_id": obj.source_id,
                        }
                    )

        summary["additional_signs_created"] += created_count
        new_details = details[details_before:]
        skipped_count = sum(1 for e in new_details if e.get("level") == "skip")
        warning_count = sum(1 for e in new_details if e.get("level") == "warning")
        logger.info(
            "_create_additional_signs: created=%d skipped=%d warnings=%d",
            created_count,
            skipped_count,
            warning_count,
        )
        self._record_phase_result(
            summary,
            "additional-signs",
            "create",
            created=created_count,
            skipped=skipped_count,
            warnings=warning_count,
        )
        self._save_run_log(summary)

    def _update_additional_signs(self, summary: dict[str, Any]) -> None:  # noqa: C901
        """Update existing AdditionalSignReal records from non-Removed CSV rows.

        Only rows whose source_id already exists in the DB and whose status is not
        ``"Removed"`` are processed. Field comparison is applied unless
        ``force_update`` is True.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["additional_signs_updated"] and phase results
                are appended.
        """
        update_source_ids = [
            s
            for s, row in self.additional_signs_by_id.items()
            if s in self.additional_sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("additional_signs_updated", 0)
        if not update_source_ids:
            self._record_phase_result(summary, "additional-signs", "update", updated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.additional_sign_source_id_to_db_id[s] for s in update_source_ids}
        existing: dict[int, Any] = {obj.pk: obj for obj in AdditionalSignReal.objects.filter(pk__in=db_id_map.values())}
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)

        update_fields = [
            "source_name",
            "location",
            "device_type_id",
            "owner",
            "parent_id",
            "signpost_real_id",
            "mount_real_id",
            "mount_type",
            "direction",
            "height",
            "condition",
            "location_specifier",
            "color",
            "additional_information",
            "scanned_at",
            "attachment_url",
            "updated_by",
            "updated_at",
        ]
        updated_count = 0
        skipped_count = 0
        batch: list[Any] = []

        for source_id in update_source_ids:
            row = self.additional_signs_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped_count += 1
                continue

            txt = row.get(CSVHeadersV2.txt, "") or ""
            if txt.strip().lower() == "unreadable":
                details.append({"level": "skip", "source_id": source_id, "reason": "text value is unreadable"})
                skipped_count += 1
                continue

            try:
                new_location = self._georeferenced_point_from_csv_row(row)
            except (KeyError, ValueError) as exc:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates on update: {exc}"}
                )
                skipped_count += 1
                continue

            if not geometry_is_legit(new_location):
                details.append(
                    {
                        "level": "skip",
                        "source_id": source_id,
                        "reason": f"Invalid location on update: {new_location.ewkt}",
                    }
                )
                skipped_count += 1
                continue

            code = row.get(CSVHeadersV2.code, "")
            device_type_id = self.code_to_device_type_id.get(code)
            if device_type_id is None:
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"}
                )
                skipped_count += 1
                continue

            mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
            new_mount_real_id = None
            if mount_csv_id:
                new_mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
                if new_mount_real_id is None:
                    details.append(
                        {
                            "level": "warning",
                            "source_id": source_id,
                            "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                        }
                    )

            parent_csv_id = row.get(CSVHeadersV2.parent_sign_id, "")
            new_parent_id, new_signpost_real_id = self._resolve_additional_sign_parent(
                parent_csv_id, source_id, details
            )

            number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
            raw_ls = row.get(CSVHeadersV2.location_specifier, "")
            new_location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
            new_mount_type = self.mount_types_by_name.get(row.get(CSVHeadersV2.sign_mount_type, ""))
            new_color = self._get_additional_sign_color(row.get(CSVHeadersV2.color))
            new_direction = self._get_sign_direction(row.get(CSVHeadersV2.direction))
            new_height = self._get_sign_height(row.get(CSVHeadersV2.height))
            new_condition = self._get_sign_condition(row.get(CSVHeadersV2.condition))
            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at))
            new_attachment_url = row.get(CSVHeadersV2.attachment_url, "")
            new_source_name = "StreetScan2025"
            internal_info = row.get("internal_additional_info")
            new_additional_information = self._build_additional_information(txt, number_code_str, internal_info)

            changed = (
                self.force_update
                or obj.source_name != new_source_name
                or obj.location != new_location
                or obj.device_type_id != device_type_id
                or obj.parent_id != new_parent_id
                or obj.signpost_real_id != new_signpost_real_id
                or obj.mount_real_id != new_mount_real_id
                or obj.mount_type_id != (new_mount_type.pk if new_mount_type else None)
                or obj.direction != new_direction
                or obj.height != new_height
                or obj.condition != new_condition
                or obj.location_specifier != new_location_specifier
                or obj.color != new_color
                or obj.additional_information != new_additional_information
                or obj.scanned_at != new_scanned_at
                or obj.attachment_url != new_attachment_url
            )
            if not changed:
                skipped_count += 1
                continue

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "update",
                        "object_type": "AdditionalSignReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "old": {
                            "source_name": obj.source_name,
                            "location": obj.location.ewkt if obj.location else None,
                            "device_type_id": obj.device_type_id,
                            "parent_id": obj.parent_id,
                            "signpost_real_id": obj.signpost_real_id,
                            "mount_real_id": obj.mount_real_id,
                            "direction": obj.direction,
                            "height": str(obj.height) if obj.height is not None else None,
                            "condition": obj.condition,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "attachment_url": obj.attachment_url,
                            "additional_information": obj.additional_information,
                        },
                    }
                )

            obj.source_name = new_source_name
            obj.location = new_location
            obj.device_type_id = device_type_id
            obj.owner = self.default_owner
            obj.parent_id = new_parent_id
            obj.signpost_real_id = new_signpost_real_id
            obj.mount_real_id = new_mount_real_id
            obj.mount_type = new_mount_type
            obj.direction = new_direction
            obj.height = new_height
            obj.condition = new_condition
            obj.location_specifier = new_location_specifier
            obj.color = new_color
            obj.additional_information = new_additional_information
            obj.scanned_at = new_scanned_at
            obj.attachment_url = new_attachment_url
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            batch.append(obj)

            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    AdditionalSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
                updated_count += len(batch)
                batch = []

        if batch:
            if not self.dry_run:
                AdditionalSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
            updated_count += len(batch)

        skipped_count += sum(1 for e in details[details_before:] if e.get("level") == "skip")
        summary["additional_signs_updated"] += updated_count
        logger.info(
            "_update_additional_signs: updated=%d skipped=%d (of %d candidates)",
            updated_count,
            skipped_count,
            len(update_source_ids),
        )
        self._record_phase_result(summary, "additional-signs", "update", updated=updated_count, skipped=skipped_count)
        self._save_run_log(summary)

    def _deactivate_additional_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate AdditionalSignReal records whose CSV status is ``Removed``.

        Sets ``lifecycle`` → ``Lifecycle.INACTIVE``,
        ``validity_period_end`` → date from CSV ``scanned_at`` (``None`` if absent),
        ``scanned_at`` → CSV timestamp, ``source_name`` → ``"StreetScan2025"``,
        ``updated_by`` and ``updated_at``. No other fields are modified.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["additional_signs_deactivated"] and phase
                results are appended.
        """
        deactivate_source_ids = [
            s
            for s, row in self.additional_signs_by_id.items()
            if s in self.additional_sign_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("additional_signs_deactivated", 0)
        if not deactivate_source_ids:
            self._record_phase_result(summary, "additional-signs", "deactivate", deactivated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map: dict[str, int] = {s: self.additional_sign_source_id_to_db_id[s] for s in deactivate_source_ids}
        existing: dict[int, Any] = {obj.pk: obj for obj in AdditionalSignReal.objects.filter(pk__in=db_id_map.values())}
        update_fields = ["lifecycle", "validity_period_end", "scanned_at", "source_name", "updated_by", "updated_at"]
        batch: list[Any] = []
        deactivated_count = 0

        for source_id in deactivate_source_ids:
            row = self.additional_signs_by_id[source_id]
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                continue

            new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at))
            validity_end = new_scanned_at.date() if new_scanned_at else None

            if not self.dry_run:
                self._write_revert_record(
                    {
                        "action": "deactivate",
                        "object_type": "AdditionalSignReal",
                        "db_id": str(obj.pk),
                        "source_id": source_id,
                        "before": {
                            "lifecycle": obj.lifecycle,
                            "validity_period_end": str(obj.validity_period_end) if obj.validity_period_end else None,
                            "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
                            "source_name": obj.source_name,
                        },
                    }
                )

            obj.lifecycle = Lifecycle.INACTIVE
            obj.validity_period_end = validity_end
            obj.scanned_at = new_scanned_at
            obj.source_name = "StreetScan2025"
            obj.updated_by = self.user
            obj.updated_at = phase_started_at
            batch.append(obj)

            if len(batch) >= self.batch_size:
                if not self.dry_run:
                    AdditionalSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
                deactivated_count += len(batch)
                batch = []

        if batch:
            if not self.dry_run:
                AdditionalSignReal.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
            deactivated_count += len(batch)

        summary["additional_signs_deactivated"] += deactivated_count
        logger.info(
            "_deactivate_additional_signs: deactivated=%d (of %d candidates)",
            deactivated_count,
            len(deactivate_source_ids),
        )
        self._record_phase_result(summary, "additional-signs", "deactivate", deactivated=deactivated_count, skipped=0)
        self._save_run_log(summary)
