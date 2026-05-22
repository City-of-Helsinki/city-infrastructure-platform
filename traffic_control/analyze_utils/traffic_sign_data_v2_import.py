"""V2 traffic sign importer.

Handles create, update and deactivate operations for MountReal, TrafficSignReal,
SignpostReal and AdditionalSignReal based on enriched V2 CSV data.

This module is intentionally kept separate from the analysis pipeline so that
the management command can run an import without triggering the full analysis.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import tempfile
from collections.abc import Callable, Generator
from typing import Any

from django.core.files import File

from traffic_control.analyze_utils.traffic_sign_data_v2_code_transform import CodeTransformMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2
from traffic_control.analyze_utils.traffic_sign_data_v2_data_loading import DataLoadingMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_db_builders import DbBuilderMixin
from traffic_control.enums import InstallationStatus
from traffic_control.geometry_utils import geometry_is_legit
from traffic_control.models import MountReal, MountType, Owner
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier
from traffic_control.models.streetscan_import import StreetScanImportRevertFile, StreetScanImportRun
from users.models import User

logger = logging.getLogger(__name__)

# Valid values for the --object-type and --phase CLI arguments.
VALID_OBJECT_TYPES: tuple[str, ...] = ("mounts", "signs", "signposts", "additional-signs")
VALID_PHASES: tuple[str, ...] = ("create", "update", "deactivate")

# Dependency order — object types must be processed in this sequence.
OBJECT_TYPE_ORDER: tuple[str, ...] = ("mounts", "signs", "signposts", "additional-signs")

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
        self.phases: list[str] = list(phases)

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

        # --- DB PK maps (source_id → db pk) ---
        # Used for update and deactivate FK resolution.
        self.mount_source_id_to_db_id: dict = self._build_mount_source_id_to_db_id()
        self.sign_source_id_to_db_id: dict = self._build_sign_source_id_to_db_id()
        self.additional_sign_source_id_to_db_id: dict = self._build_additional_sign_source_id_to_db_id()
        self.signpost_source_id_to_db_id: dict = self._build_signpost_source_id_to_db_id()

        # Record total preprocessing wall-clock time (CSV I/O + enrichment + DB map builds).
        self._preprocessing_duration_s: float = (datetime.datetime.now() - _t_preprocess_start).total_seconds()

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
        skipped_count = len(summary.get("details", [])) - details_before
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
        mount_types_by_name: dict[str, MountType] = {
            **{mt.description_fi: mt for mt in MountType.objects.all()},
            **{mt.description: mt for mt in MountType.objects.all()},
        }
        default_owner = self._get_default_owner()
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
            mount_type = mount_types_by_name.get(mount_type_name)

            processed.append(source_id)
            yield MountReal(
                source_id=source_id,
                source_name="StreetScan2025",
                location=location,
                owner=default_owner,
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

    @staticmethod
    def _get_default_owner() -> Owner:
        """Return the default Owner instance (Helsingin kaupunki).

        Returns:
            Owner: The default owner object.
        """

        return Owner.objects.get(name_fi="Helsingin kaupunki")

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
        run_log = StreetScanImportRun(
            is_dry_run=self.dry_run,
            mount_file=self.mount_file,
            sign_file=self.sign_file,
            preprocessing_duration_s=self._preprocessing_duration_s,
        )
        run_log.save()
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

        # Extract phase durations from phase_results into the dedicated field.
        phase_durations: dict[str, dict[str, float]] = {}
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
            filename = f"revert_{self.run_log.ran_at:%Y%m%d_%H%M%S}_{self.run_log.pk}.jsonl"
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
        mount_types_by_name: dict[str, MountType],
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
            mount_types_by_name (dict[str, MountType]): MountType lookup by name.
            summary (dict[str, Any]): Mutable summary dict; skips are appended to
                summary["details"] and summary["skipped_mount_update_count"] is
                incremented.
            phase_started_at (datetime.datetime): Timestamp of phase start, used as updated_at.

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
            new_mount_type = mount_types_by_name.get(row.get(CSVHeadersV2.mount_type, ""))
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
        mount_types_by_name: dict[str, MountType] = {
            **{mt.description_fi: mt for mt in MountType.objects.all()},
            **{mt.description: mt for mt in MountType.objects.all()},
        }

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
        generator = self._get_mounts_to_update(
            update_source_ids, db_id_map, existing, mount_types_by_name, summary, phase_started_at
        )

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
    # Traffic sign handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_signs(self, summary: dict[str, Any]) -> None:
        """Create new TrafficSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signs_by_id.items()
                if s not in self.sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info("[TODO] _create_signs — %d new rows (not in DB, not Removed)", candidates)

    def _update_signs(self, summary: dict[str, Any]) -> None:
        """Update existing TrafficSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signs_by_id.items()
                if s in self.sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info("[TODO] _update_signs — %d rows in CSV (non-Removed) that already exist in DB", candidates)

    def _deactivate_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate TrafficSignReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signs_by_id.items()
                if s in self.sign_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
            ]
        )
        logger.info("[TODO] _deactivate_signs — %d Removed rows that exist in DB", candidates)

    # ------------------------------------------------------------------
    # Signpost handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_signposts(self, summary: dict[str, Any]) -> None:
        """Create new SignpostReal records (two-pass for parent ordering).

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signposts_by_id.items()
                if s not in self.signpost_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info("[TODO] _create_signposts — %d new rows (not in DB, not Removed)", candidates)

    def _update_signposts(self, summary: dict[str, Any]) -> None:
        """Update existing SignpostReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signposts_by_id.items()
                if s in self.signpost_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info("[TODO] _update_signposts — %d rows in CSV (non-Removed) that already exist in DB", candidates)

    def _deactivate_signposts(self, summary: dict[str, Any]) -> None:
        """Deactivate SignpostReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.signposts_by_id.items()
                if s in self.signpost_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
            ]
        )
        logger.info("[TODO] _deactivate_signposts — %d Removed rows that exist in DB", candidates)

    # ------------------------------------------------------------------
    # Additional sign handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_additional_signs(self, summary: dict[str, Any]) -> None:
        """Create new AdditionalSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.additional_signs_by_id.items()
                if s not in self.additional_sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info("[TODO] _create_additional_signs — %d new rows (not in DB, not Removed)", candidates)

    def _update_additional_signs(self, summary: dict[str, Any]) -> None:
        """Update existing AdditionalSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.additional_signs_by_id.items()
                if s in self.additional_sign_source_id_to_db_id and row.get(CSVHeadersV2.status) != "Removed"
            ]
        )
        logger.info(
            "[TODO] _update_additional_signs — %d rows in CSV (non-Removed) that already exist in DB", candidates
        )

    def _deactivate_additional_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate AdditionalSignReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        candidates = len(
            [
                s
                for s, row in self.additional_signs_by_id.items()
                if s in self.additional_sign_source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
            ]
        )
        logger.info("[TODO] _deactivate_additional_signs — %d Removed rows that exist in DB", candidates)
