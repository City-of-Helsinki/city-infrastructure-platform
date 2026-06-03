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
from collections.abc import Callable, KeysView, Set as AbstractSet
from decimal import Decimal
from typing import Any
from uuid import UUID

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

# Source name for all imported records.
SOURCE_NAME: str = "StreetScan2025"

# Dependency order — object types must be processed in this sequence.
OBJECT_TYPE_ORDER: tuple[str, ...] = ("mounts", "signs", "signposts", "additional-signs")
# Phase order
PHASE_ORDER: tuple[str, ...] = ("create", "update", "deactivate")

# Mounts are never deactivated; the deactivate phase is silently skipped for them.
_DEACTIVATABLE_OBJECT_TYPES: frozenset[str] = frozenset({"signs", "signposts", "additional-signs"})

# Suffix appended to geometry validation error messages during update phases.
_ON_UPDATE_SUFFIX: str = " on update"


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

    def _run_phase(self, object_type: str, phase: str, summary: dict[str, Any]) -> None:
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

    def _build_mount_for_create(
        self,
        source_id: str,
        row: dict[str, Any],
        location: Any,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> MountReal:
        """Build an unsaved MountReal instance from a CSV row.

        Args:
            source_id (str): Source identifier.
            row (dict[str, Any]): CSV row for this source_id.
            location (Any): Already-validated geometry point.
            details (list[dict]): Mutable details list (unused for mounts, present for API consistency).
            phase_started_at (datetime.datetime): Timestamp used as ``created_at``.

        Returns:
            MountReal: Unsaved MountReal instance ready for bulk_create.
        """
        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        return MountReal(
            source_id=source_id,
            source_name=SOURCE_NAME,
            location=location,
            owner=self.default_owner,
            installation_status=InstallationStatus.IN_USE,
            location_specifier=MountLocationSpecifier(int(raw_ls)) if raw_ls else None,
            mount_type=self.mount_types_by_name.get(row.get(CSVHeadersV2.mount_type, "")),
            scanned_at=self._get_scanned_at(row.get(CSVHeadersV2.mount_scanned_at), source_id, details),
            attachment_url=row.get(CSVHeadersV2.attachment_url, ""),
            created_by=self.user,
            created_at=phase_started_at,
        )

    def _iter_objects_to_create(
        self,
        rows_by_id: dict[str, Any],
        existing_source_ids: AbstractSet[str],
        details: list[dict],
        processed: list[str],
        build_object: Callable[[str, dict[str, Any], Any, list[dict], datetime.datetime], Any],
        phase_started_at: datetime.datetime,
        filter_removed: bool = True,
    ) -> Any:
        """Yield unsaved model instances for the create phase.

        Memory-efficient generator consumed by ``bulk_create`` in ``_create_objects``.
        Django pulls exactly ``batch_size`` items at a time from the generator so
        peak Python memory stays at O(batch_size) rather than O(total rows).

        Args:
            rows_by_id (dict[str, Any]): CSV rows keyed by source_id.
            existing_source_ids (AbstractSet[str]): Source IDs already in the DB (skipped).
            details (list[dict]): Mutable details list for skip/warning entries.
            processed (list[str]): Mutable list to append successfully prepared source_ids.
            build_object (Callable): Per-row factory ``(source_id, row, location, details,
                phase_started_at) -> model instance | None``. Return None to skip.
            phase_started_at (datetime.datetime): Timestamp used as ``created_at``.
            filter_removed (bool): When True (default), rows with status ``"Removed"``
                are excluded. Set to False for mounts.

        Yields:
            Unsaved model instances ready for ``bulk_create``.
        """
        for source_id, row in rows_by_id.items():
            if source_id in existing_source_ids:
                continue
            if filter_removed and row.get(CSVHeadersV2.status) == "Removed":
                continue
            location = self._validate_and_get_location(row, source_id, details)
            if location is None:
                continue
            obj = build_object(source_id, row, location, details, phase_started_at)
            if obj is None:
                continue
            processed.append(source_id)
            yield obj

    def _create_objects(
        self,
        summary: dict[str, Any],
        rows_by_id: dict[str, Any],
        existing_source_ids: AbstractSet[str],
        model_class: type,
        object_type: str,
        summary_key: str,
        object_type_name: str,
        processed_key: str,
        build_object: Callable[[str, dict[str, Any], Any, list[dict], datetime.datetime], Any],
        filter_removed: bool = True,
    ) -> None:
        """Generic create phase handler shared by mounts, signs and additional signs.

        Uses a generator so Django's ``bulk_create`` processes rows in batches of
        ``batch_size``, keeping peak Python memory at O(batch_size) rather than
        O(total rows).

        Args:
            summary (dict[str, Any]): Mutable summary dict.
            rows_by_id (dict[str, Any]): CSV rows keyed by source_id.
            existing_source_ids (AbstractSet[str]): Source IDs already in the DB.
            model_class (type): Django model class to bulk_create.
            object_type (str): Object type label used in phase results (e.g. ``"mounts"``).
            summary_key (str): Key in summary dict for created count (e.g. ``"mounts_created"``).
            object_type_name (str): Model class name used in revert records (e.g. ``"MountReal"``).
            processed_key (str): Key in summary dict for processed source_id list.
            build_object (Callable): ``(source_id, row, location, details, phase_started_at)
                -> model instance | None``. Return None to skip the row.
            filter_removed (bool): When True (default), rows with status ``"Removed"``
                are excluded. Set to False for mounts which have no status field.
        """
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault(summary_key, 0)
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)
        processed: list[str] = summary.setdefault(processed_key, [])

        total_candidates = sum(
            1
            for s, row in rows_by_id.items()
            if s not in existing_source_ids and (not filter_removed or row.get(CSVHeadersV2.status) != "Removed")
        )
        generator = self._iter_objects_to_create(
            rows_by_id, existing_source_ids, details, processed, build_object, phase_started_at, filter_removed
        )
        if self.dry_run:
            created_count = sum(1 for _ in generator)
        else:
            created = model_class.objects.bulk_create(generator, batch_size=self.batch_size)
            created_count = len(created)
            for obj in created:
                self._write_revert_record(
                    {
                        "action": "create",
                        "object_type": object_type_name,
                        "db_id": str(obj.id),
                        "source_id": obj.source_id,
                    }
                )

        summary[summary_key] += created_count
        new_details = details[details_before:]
        self._stamp_object_type(details, details_before, object_type, "create")
        skipped_count = sum(1 for e in new_details if e.get("level") == "skip")
        warning_count = sum(1 for e in new_details if e.get("level") == "warning")
        logger.info(
            "_%s: created=%d skipped=%d warnings=%d (of %d candidates)",
            f"create_{object_type.replace('-', '_')}",
            created_count,
            skipped_count,
            warning_count,
            total_candidates,
        )
        self._record_phase_result(
            summary, object_type, "create", created=created_count, skipped=skipped_count, warnings=warning_count
        )
        self._save_run_log(summary)

    def _create_mounts(self, summary: dict[str, Any]) -> None:
        """Create new MountReal records from CSV rows not yet in the DB.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip entries are
                appended to summary["details"] and summary["mounts_created"] is
                incremented.
        """
        self._create_objects(
            summary,
            rows_by_id=self.mounts_by_id,
            existing_source_ids=self.mount_source_id_to_db_id.keys(),
            model_class=MountReal,
            object_type="mounts",
            summary_key="mounts_created",
            object_type_name="MountReal",
            processed_key="processed_mount_source_ids",
            build_object=self._build_mount_for_create,
            filter_removed=False,
        )

    def _get_scanned_at(self, date_str: str | None, source_id: str, details: list[dict]) -> datetime.datetime | None:
        """Parse the scanned_at timestamp from a CSV row value.

        Both mount and sign CSVs use the format ``2025/08/27 08:17:40+00``
        (slash-separated date, space separator, truncated timezone offset).
        Appending ``"00"`` before parsing corrects the truncated ``+00`` marker
        to a valid ``+0000`` offset.

        Args:
            date_str (str | None): Raw timestamp string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            datetime.datetime | None: Parsed UTC-aware datetime, or None if absent/unparseable.
        """
        if not date_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "scanned_at is absent or empty"})
            return None
        try:
            return datetime.datetime.strptime(date_str.strip() + "00", "%Y/%m/%d %H:%M:%S%z")
        except ValueError:
            details.append(
                {"level": "warning", "source_id": source_id, "reason": f"Could not parse scanned_at={date_str!r}"}
            )
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
    def _stamp_object_type(details: list[dict], from_index: int, object_type: str, phase: str) -> None:
        """Stamp ``object_type`` and ``phase`` onto all details entries added during a phase.

        Called immediately after each create/update/deactivate phase so that every
        warning, skip, or error entry in the run log carries enough context for
        grouped display in the admin.

        Args:
            details (list[dict]): The full details list from the summary dict.
            from_index (int): Index of the first entry written during this phase.
            object_type (str): One of VALID_OBJECT_TYPES (e.g. ``"signs"``).
            phase (str): One of VALID_PHASES (e.g. ``"create"``).
        """
        for entry in details[from_index:]:
            entry["object_type"] = object_type
            entry["phase"] = phase

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

    def _mount_fields_changed(
        self,
        obj: MountReal,
        new_location: Any,
        fields: dict[str, Any],
    ) -> bool:
        """Check if any mount fields have changed from stored DB values.

        Args:
            obj (MountReal): Existing MountReal DB instance.
            new_location (Any): New geometry point.
            fields (dict[str, Any]): Resolved field values from ``_resolve_mount_new_fields``,
                containing ``location_specifier``, ``mount_type``, ``scanned_at`` and
                ``attachment_url``.

        Returns:
            bool: True if any field has changed or force_update is set.
        """
        if self.force_update:
            return True
        new_mount_type = fields["mount_type"]
        comparisons: list[tuple[Any, Any]] = [
            (obj.source_name, SOURCE_NAME),
            (obj.scanned_at, fields["scanned_at"]),
            (obj.location, new_location),
            (obj.location_specifier, fields["location_specifier"]),
            (obj.mount_type_id, new_mount_type.pk if new_mount_type else None),
            (obj.attachment_url, fields["attachment_url"]),
        ]
        return any(old != new for old, new in comparisons)

    def _resolve_mount_new_fields(self, row: dict[str, Any], source_id: str, details: list[dict]) -> dict[str, Any]:
        """Resolve new field values for a MountReal update from a CSV row.

        Args:
            row (dict[str, Any]): A single CSV row keyed by CSVHeadersV2 constants.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list for warning entries.

        Returns:
            dict[str, Any]: Resolved field values with keys ``location_specifier``,
                ``mount_type``, ``scanned_at``, and ``attachment_url``.
        """
        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        return {
            "location_specifier": MountLocationSpecifier(int(raw_ls)) if raw_ls else None,
            "mount_type": self.mount_types_by_name.get(row.get(CSVHeadersV2.mount_type, "")),
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.mount_scanned_at), source_id, details),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
        }

    def _write_mount_update_revert_record(self, obj: MountReal, source_id: str) -> None:
        """Write a revert record capturing the current state of a MountReal before update.

        Args:
            obj (MountReal): The MountReal instance about to be updated.
            source_id (str): The source identifier for this mount.
        """
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

    def _prepare_mount_for_update(
        self,
        obj: MountReal,
        row: dict[str, Any],
        source_id: str,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> bool:
        """Mutate a MountReal instance in-place with new CSV values.

        Args:
            obj (MountReal): Existing DB instance to mutate.
            row (dict[str, Any]): CSV row for this source_id.
            source_id (str): Source identifier used for error reporting.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``updated_at``.

        Returns:
            bool: True if the object was mutated and should be bulk-updated, False to skip.
        """
        new_location = self._validate_and_get_location(row, source_id, details, _ON_UPDATE_SUFFIX)
        fields = self._resolve_mount_new_fields(row, source_id, details)
        if new_location is None or not self._mount_fields_changed(obj, new_location, fields):
            return False
        if not self.dry_run:
            self._write_mount_update_revert_record(obj, source_id)
        obj.source_name = SOURCE_NAME
        obj.location = new_location
        obj.location_specifier = fields["location_specifier"]
        obj.mount_type = fields["mount_type"]
        obj.scanned_at = fields["scanned_at"]
        obj.attachment_url = fields["attachment_url"]
        obj.updated_by = self.user
        obj.updated_at = phase_started_at
        return True

    def _flush_update_batch(
        self,
        batch: list[Any],
        model_class: type,
        update_fields: list[str],
    ) -> int:
        """Persist a batch of mutated model instances via bulk_update and return the count.

        A no-op (returns the batch length without writing) when ``dry_run`` is True.

        Args:
            batch (list[Any]): Mutated model instances to persist.
            model_class (type): Django model class with an ``objects`` manager.
            update_fields (list[str]): Field names passed to ``bulk_update``.

        Returns:
            int: Number of objects in the batch (same whether dry run or not).
        """
        if not self.dry_run:
            model_class.objects.bulk_update(batch, update_fields, batch_size=self.batch_size)
        return len(batch)

    def _update_objects(
        self,
        summary: dict[str, Any],
        rows_by_id: dict[str, Any],
        source_id_to_db_id: dict[str, Any],
        model_class: type,
        object_type: str,
        summary_key: str,
        update_fields: list[str],
        prepare_row: Callable[[Any, dict[str, Any], str, list[dict], datetime.datetime], bool],
        filter_removed: bool = True,
    ) -> None:
        """Generic update phase handler shared by all four object types.

        Filters candidate source_ids, fetches current DB state, calls ``prepare_row``
        for each candidate to mutate the object in-place (or signal skip), and
        bulk-updates mutated objects in batches.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
            rows_by_id (dict[str, Any]): CSV rows keyed by source_id.
            source_id_to_db_id (dict[str, Any]): Mapping from source_id to DB primary key.
            model_class (type): Django model class to query and bulk_update.
            object_type (str): Object type label used in phase results (e.g. ``"signs"``).
            summary_key (str): Key in summary dict for updated count (e.g. ``"signs_updated"``).
            update_fields (list[str]): Field names passed to bulk_update.
            prepare_row (Callable): Per-row callback ``(obj, row, source_id, details,
                phase_started_at) -> bool``. Returns True if the object was mutated and
                should be saved, False to skip.
            filter_removed (bool): When True (default), rows with status ``"Removed"``
                are excluded. Set to False for mounts which have no status field.
        """
        update_source_ids = [
            s
            for s, row in rows_by_id.items()
            if s in source_id_to_db_id and (not filter_removed or row.get(CSVHeadersV2.status) != "Removed")
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault(summary_key, 0)
        if not update_source_ids:
            self._record_phase_result(summary, object_type, "update", updated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map = {s: source_id_to_db_id[s] for s in update_source_ids}
        existing = {obj.pk: obj for obj in model_class.objects.filter(pk__in=db_id_map.values())}
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)
        updated_count = 0
        skipped_count = 0
        batch: list[Any] = []

        for source_id in update_source_ids:
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped_count += 1
                continue
            if prepare_row(obj, rows_by_id[source_id], source_id, details, phase_started_at):
                batch.append(obj)
                if len(batch) >= self.batch_size:
                    updated_count += self._flush_update_batch(batch, model_class, update_fields)
                    batch = []
            else:
                skipped_count += 1

        if batch:
            updated_count += self._flush_update_batch(batch, model_class, update_fields)

        summary[summary_key] += updated_count
        self._stamp_object_type(details, details_before, object_type, "update")
        logger.info(
            "_%s: updated=%d skipped=%d (of %d candidates)",
            f"update_{object_type.replace('-', '_')}",
            updated_count,
            skipped_count,
            len(update_source_ids),
        )
        self._record_phase_result(summary, object_type, "update", updated=updated_count, skipped=skipped_count)
        self._save_run_log(summary)

    def _update_mounts(self, summary: dict[str, Any]) -> None:
        """Update existing MountReal records from CSV rows whose source_id is already in the DB.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["mounts_updated"] and phase results are appended.
        """
        self._update_objects(
            summary,
            rows_by_id=self.mounts_by_id,
            source_id_to_db_id=self.mount_source_id_to_db_id,
            model_class=MountReal,
            object_type="mounts",
            summary_key="mounts_updated",
            update_fields=[
                "source_name",
                "location",
                "location_specifier",
                "mount_type",
                "scanned_at",
                "attachment_url",
                "updated_by",
                "updated_at",
            ],
            prepare_row=self._prepare_mount_for_update,
            filter_removed=False,
        )

    # ------------------------------------------------------------------
    # Traffic sign field-cast helpers
    # ------------------------------------------------------------------

    def _get_sign_height(self, height_str: str | None, source_id: str, details: list[dict]) -> int | None:
        """Convert height from metres (CSV) to centimetres (DB integer).

        Args:
            height_str (str | None): Raw height string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            int | None: Height in centimetres, or None if absent/unparseable.
        """
        if not height_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "height is absent or empty"})
            return None
        try:
            return int(float(height_str) * 100)
        except (ValueError, TypeError):
            details.append(
                {"level": "warning", "source_id": source_id, "reason": f"Could not parse height={height_str!r}"}
            )
            return None

    def _get_sign_direction(self, direction_str: str | None, source_id: str, details: list[dict]) -> int | None:
        """Parse azimuth direction from CSV as integer degrees.

        Args:
            direction_str (str | None): Raw direction string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            int | None: Direction in degrees, or None if absent/unparseable.
        """
        if not direction_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "direction is absent or empty"})
            return None
        try:
            return int(float(direction_str))
        except (ValueError, TypeError):
            details.append(
                {"level": "warning", "source_id": source_id, "reason": f"Could not parse direction={direction_str!r}"}
            )
            return None

    def _get_sign_condition(self, condition_str: str | None, source_id: str, details: list[dict]) -> Condition | None:
        """Parse condition from CSV as Condition enum.

        Args:
            condition_str (str | None): Raw condition string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            Condition | None: Parsed Condition enum value, or None if absent/unparseable.
        """
        if not condition_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "condition is absent or empty"})
            return None
        try:
            return Condition(int(condition_str))
        except (ValueError, TypeError):
            details.append(
                {"level": "warning", "source_id": source_id, "reason": f"Could not parse condition={condition_str!r}"}
            )
            return None

    def _get_sign_value(self, number_code_str: str | None, source_id: str, details: list[dict]) -> Decimal | None:
        """Extract the leading numeric value from number_code field as Decimal.

        Args:
            number_code_str (str | None): Raw number_code string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            Decimal | None: Extracted value, or None if absent/no numeric prefix found.
        """
        if not number_code_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "number_code is absent or empty"})
            return None
        match = NUMBER_CODE_PATTERN.match(number_code_str.strip())
        try:
            return Decimal(match.group(1)) if match else None
        except Exception:
            details.append(
                {
                    "level": "warning",
                    "source_id": source_id,
                    "reason": f"Could not parse value from number_code={number_code_str!r}",
                }
            )
            return None

    def _validate_and_get_location(
        self,
        row: dict,
        source_id: str,
        details: list[dict],
        operation: str = "",
    ) -> Any | None:
        """Validate and return a georeferenced point from a CSV row.

        Performs two-stage validation: first parses coordinates from the row,
        then validates the resulting geometry. If either stage fails, appends
        a skip-level detail entry and returns None.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier for error reporting.
            details (list[dict]): Mutable list to append skip entries to.
            operation (str): Optional suffix for error messages (e.g., " on update").

        Returns:
            Any | None: Valid Point geometry, or None if validation failed.
        """
        try:
            location = self._georeferenced_point_from_csv_row(row)
        except (KeyError, ValueError) as exc:
            details.append(
                {"level": "skip", "source_id": source_id, "reason": f"Invalid coordinates{operation}: {exc}"}
            )
            return None

        if not geometry_is_legit(location):
            details.append(
                {"level": "skip", "source_id": source_id, "reason": f"Invalid location{operation}: {location.ewkt}"}
            )
            return None

        return location

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
                "Required Owner 'Helsingin kaupunki' not found in the database. Cannot proceed with import."
            )
        try:
            private_owner = Owner.objects.get(name_fi="Yksityinen")
        except Owner.DoesNotExist:
            raise RuntimeError("Required Owner 'Yksityinen' not found in the database. Cannot proceed with import.")
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

    def _resolve_device_type_id(self, row: dict, source_id: str, details: list[dict]) -> int | None:
        """Resolve and validate the device type id from a CSV row code field.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier.
            details (list[dict]): Mutable details list; a skip entry is appended when the
                code is not found.

        Returns:
            int | None: Device type DB id, or None if the code was not found (skip appended).
        """
        code = row.get(CSVHeadersV2.code, "")
        device_type_id = self.code_to_device_type_id.get(code)
        if device_type_id is None:
            details.append({"level": "skip", "source_id": source_id, "reason": f"Device type code not found: {code}"})
        return device_type_id

    def _resolve_mount_real_id(self, row: dict, source_id: str, details: list[dict]) -> int | None:
        """Resolve the mount real DB id from a CSV row mount_id field.

        Appends a warning entry to ``details`` when the CSV mount id is present but
        cannot be found in the DB map. Returns ``None`` when the CSV field is absent
        or the mount is not found.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier.
            details (list[dict]): Mutable details list; a warning entry is appended when
                the mount is absent from the DB map.

        Returns:
            int | None: Mount real DB id, or None if mount CSV id is absent or not in DB.
        """
        mount_csv_id = row.get(CSVHeadersV2.mount_id, "")
        if not mount_csv_id:
            return None
        mount_real_id = self.mount_source_id_to_db_id.get(mount_csv_id)
        if mount_real_id is None:
            details.append(
                {
                    "level": "warning",
                    "source_id": source_id,
                    "reason": f"Mount not found for mount CSV id: {mount_csv_id}",
                }
            )
        return mount_real_id

    def _resolve_sign_fields(
        self,
        row: dict,
        source_id: str,
        details: list[dict],
    ) -> dict[str, Any] | None:
        """Resolve and validate all field values for a traffic sign create or update row.

        Validates device type code, resolves FK ids (mount), checks for parent_sign_id
        warning, resolves owner, and casts all field values. Returns ``None`` and appends
        a skip entry when a hard validation error is encountered. Mount/parent warnings
        are appended but do not cause a skip.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier.
            details (list[dict]): Mutable details list for skip/warning entries.

        Returns:
            dict[str, Any] | None: Resolved field dict, or None if row must be skipped.
        """
        code = row.get(CSVHeadersV2.code, "")  # also needed for _resolve_sign_owner below
        device_type_id = self._resolve_device_type_id(row, source_id, details)
        if device_type_id is None:
            return None

        mount_real_id = self._resolve_mount_real_id(row, source_id, details)

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
        value = self._get_sign_value(number_code_str, source_id, details)
        owner = self._resolve_sign_owner(code, number_code_str)

        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
        sign_mount_type_name = row.get(CSVHeadersV2.sign_mount_type, "")
        mount_type = self.mount_types_by_name.get(sign_mount_type_name)

        return {
            "device_type_id": device_type_id,
            "mount_real_id": mount_real_id,
            "mount_type": mount_type,
            "owner": owner,
            "location_specifier": location_specifier,
            "value": value,
            "direction": self._get_sign_direction(row.get(CSVHeadersV2.direction), source_id, details),
            "height": self._get_sign_height(row.get(CSVHeadersV2.height), source_id, details),
            "condition": self._get_sign_condition(row.get(CSVHeadersV2.condition), source_id, details),
            "txt": row.get(CSVHeadersV2.txt, "") or None,
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.scanned_at), source_id, details),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
        }

    def _create_deactivation_revert_record(
        self,
        object_type: str,
        obj: Any,
        source_id: str,
    ) -> None:
        """Create and write a revert record for a deactivation operation.

        Args:
            object_type (str): Model name (e.g., "TrafficSignReal").
            obj (Any): DB object being deactivated.
            source_id (str): Source identifier.
        """
        self._write_revert_record(
            {
                "action": "deactivate",
                "object_type": object_type,
                "db_id": str(obj.pk),
                "source_id": source_id,
                "old": {
                    "lifecycle": str(obj.lifecycle),
                    "validity_period_end": str(obj.validity_period_end) if obj.validity_period_end else None,
                },
            }
        )

    def _apply_deactivation(
        self,
        obj: Any,
        row: dict,
        source_id: str,
        object_type: str,
        phase_started_at: datetime.datetime,
        details: list[dict],
    ) -> None:
        """Apply deactivation fields to an object and create revert record.

        Args:
            obj (Any): DB object to deactivate (TrafficSignReal, SignpostReal, etc.).
            row (dict): CSV row data.
            source_id (str): Source identifier.
            object_type (str): Model name for revert record.
            phase_started_at (datetime.datetime): Timestamp for updated_at field.
            details (list[dict]): Mutable details list for warning entries.
        """
        new_scanned_at = self._get_scanned_at(row.get(CSVHeadersV2.scanned_at), source_id, details)
        validity_end = new_scanned_at.date() if new_scanned_at else None

        if not self.dry_run:
            self._create_deactivation_revert_record(object_type, obj, source_id)

        obj.lifecycle = Lifecycle.INACTIVE
        obj.validity_period_end = validity_end
        obj.scanned_at = new_scanned_at
        obj.source_name = SOURCE_NAME
        obj.updated_by = self.user
        obj.updated_at = phase_started_at

    # ------------------------------------------------------------------
    # Traffic sign handlers
    # ------------------------------------------------------------------

    def _build_sign_for_create(
        self,
        source_id: str,
        row: dict[str, Any],
        location: Any,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> TrafficSignReal | None:
        """Build an unsaved TrafficSignReal instance from a CSV row.

        Args:
            source_id (str): Source identifier.
            row (dict[str, Any]): CSV row for this source_id.
            location (Any): Already-validated geometry point.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``created_at``.

        Returns:
            TrafficSignReal | None: Unsaved instance, or None if row must be skipped.
        """
        fields = self._resolve_sign_fields(row, source_id, details)
        if fields is None:
            return None
        return TrafficSignReal(
            source_id=source_id,
            source_name=SOURCE_NAME,
            location=location,
            device_type_id=fields["device_type_id"],
            owner=fields["owner"],
            installation_status=InstallationStatus.IN_USE,
            lifecycle=Lifecycle.ACTIVE,
            mount_real_id=fields["mount_real_id"],
            mount_type=fields["mount_type"],
            direction=fields["direction"],
            height=fields["height"],
            condition=fields["condition"],
            location_specifier=fields["location_specifier"],
            value=fields["value"],
            txt=fields["txt"],
            scanned_at=fields["scanned_at"],
            attachment_url=fields["attachment_url"],
            created_by=self.user,
            created_at=phase_started_at,
        )

    def _create_signs(self, summary: dict[str, Any]) -> None:
        """Create new TrafficSignReal records from CSV rows not yet in the DB.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries are
                appended to summary["details"] and summary["signs_created"] is
                incremented.
        """
        self._create_objects(
            summary,
            rows_by_id=self.signs_by_id,
            existing_source_ids=self.sign_source_id_to_db_id.keys(),
            model_class=TrafficSignReal,
            object_type="signs",
            summary_key="signs_created",
            object_type_name="TrafficSignReal",
            processed_key="processed_sign_source_ids",
            build_object=self._build_sign_for_create,
        )

    def _sign_fields_changed(self, obj: Any, new_location: Any, fields: dict[str, Any]) -> bool:
        """Check if any traffic sign fields have changed from stored DB values.

        Args:
            obj (Any): Existing TrafficSignReal DB instance.
            new_location (Any): New geometry point.
            fields (dict[str, Any]): Dictionary containing new field values.

        Returns:
            bool: True if any field has changed or force_update is set.
        """
        if self.force_update:
            return True

        new_mount_type = fields["mount_type"]
        comparisons: list[tuple[Any, Any]] = [
            (obj.source_name, SOURCE_NAME),
            (obj.location, new_location),
            (obj.device_type_id, fields["device_type_id"]),
            (obj.mount_real_id, fields["mount_real_id"]),
            (obj.mount_type_id, new_mount_type.pk if new_mount_type else None),
            (obj.direction, fields["direction"]),
            (obj.height, fields["height"]),
            (obj.condition, fields["condition"]),
            (obj.location_specifier, fields["location_specifier"]),
            (obj.value, fields["value"]),
            (obj.txt, fields["txt"]),
            (obj.scanned_at, fields["scanned_at"]),
            (obj.attachment_url, fields["attachment_url"]),
        ]
        return any(old != new for old, new in comparisons)

    def _create_sign_update_revert_record(self, obj: Any, source_id: str) -> None:
        """Create and write a revert record for a traffic sign update operation.

        Args:
            obj (Any): Existing TrafficSignReal DB instance being updated.
            source_id (str): Source identifier.
        """
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

    def _prepare_sign_for_update(
        self,
        obj: TrafficSignReal,
        row: dict[str, Any],
        source_id: str,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> bool:
        """Mutate a TrafficSignReal instance in-place with new CSV values.

        Args:
            obj (TrafficSignReal): Existing DB instance to mutate.
            row (dict[str, Any]): CSV row for this source_id.
            source_id (str): Source identifier used for error reporting.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``updated_at``.

        Returns:
            bool: True if the object was mutated and should be bulk-updated, False to skip.
        """
        new_location = self._validate_and_get_location(row, source_id, details, _ON_UPDATE_SUFFIX)
        fields = self._resolve_sign_fields(row, source_id, details)
        if new_location is None or fields is None or not self._sign_fields_changed(obj, new_location, fields):
            return False
        if not self.dry_run:
            self._create_sign_update_revert_record(obj, source_id)
        obj.source_name = SOURCE_NAME
        obj.location = new_location
        obj.device_type_id = fields["device_type_id"]
        obj.owner = fields["owner"]
        obj.installation_status = InstallationStatus.IN_USE
        obj.lifecycle = Lifecycle.ACTIVE
        obj.mount_real_id = fields["mount_real_id"]
        obj.mount_type = fields["mount_type"]
        obj.direction = fields["direction"]
        obj.height = fields["height"]
        obj.condition = fields["condition"]
        obj.location_specifier = fields["location_specifier"]
        obj.value = fields["value"]
        obj.txt = fields["txt"]
        obj.scanned_at = fields["scanned_at"]
        obj.attachment_url = fields["attachment_url"]
        obj.updated_by = self.user
        obj.updated_at = phase_started_at
        return True

    def _update_signs(self, summary: dict[str, Any]) -> None:
        """Update existing TrafficSignReal records from CSV rows already in the DB.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["signs_updated"] and phase results are appended.
        """
        self._update_objects(
            summary,
            rows_by_id=self.signs_by_id,
            source_id_to_db_id=self.sign_source_id_to_db_id,
            model_class=TrafficSignReal,
            object_type="signs",
            summary_key="signs_updated",
            update_fields=[
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
            ],
            prepare_row=self._prepare_sign_for_update,
        )

    def _deactivate_objects(
        self,
        summary: dict[str, Any],
        rows_by_id: dict[str, Any],
        source_id_to_db_id: dict[str, Any],
        model_class: type,
        object_type: str,
        summary_key: str,
        object_type_name: str,
    ) -> None:
        """Deactivate DB records whose CSV status is ``Removed``.

        Generic implementation shared by all three deactivate phase handlers.
        Sets ``lifecycle`` → ``Lifecycle.INACTIVE``, ``validity_period_end`` →
        date from CSV ``scanned_at``, ``scanned_at`` → CSV timestamp,
        ``source_name`` → ``SOURCE_NAME``, ``updated_by`` and ``updated_at``.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
            rows_by_id (dict[str, Any]): CSV rows keyed by source_id.
            source_id_to_db_id (dict[str, Any]): Mapping from source_id to DB primary key.
            model_class (type): Django model class to query and bulk_update.
            object_type (str): Object type label used in phase results (e.g. ``"signs"``).
            summary_key (str): Key in summary dict for deactivated count (e.g. ``"signs_deactivated"``).
            object_type_name (str): Class name string used in revert records (e.g. ``"TrafficSignReal"``).
        """
        deactivate_source_ids = [
            s for s, row in rows_by_id.items() if s in source_id_to_db_id and row.get(CSVHeadersV2.status) == "Removed"
        ]
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault(summary_key, 0)
        if not deactivate_source_ids:
            self._record_phase_result(summary, object_type, "deactivate", deactivated=0, skipped=0)
            self._save_run_log(summary)
            return

        db_id_map = {s: source_id_to_db_id[s] for s in deactivate_source_ids}
        existing = {obj.pk: obj for obj in model_class.objects.filter(pk__in=db_id_map.values())}
        update_fields = ["lifecycle", "validity_period_end", "scanned_at", "source_name", "updated_by", "updated_at"]
        details: list[dict] = summary.setdefault("details", [])
        details_before = len(details)
        batch: list[Any] = []
        deactivated_count = 0
        skipped_count = 0

        for source_id in deactivate_source_ids:
            obj = existing.get(db_id_map[source_id])
            if obj is None:
                skipped_count += 1
                details.append(
                    {"level": "skip", "source_id": source_id, "reason": "DB record not found for deactivation"}
                )
                continue
            if obj.lifecycle == Lifecycle.INACTIVE:
                skipped_count += 1
                details.append({"level": "skip", "source_id": source_id, "reason": "already inactive"})
                continue
            self._apply_deactivation(obj, rows_by_id[source_id], source_id, object_type_name, phase_started_at, details)
            batch.append(obj)
            if len(batch) >= self.batch_size:
                deactivated_count += self._flush_update_batch(batch, model_class, update_fields)
                batch = []

        if batch:
            deactivated_count += self._flush_update_batch(batch, model_class, update_fields)

        summary[summary_key] += deactivated_count
        self._stamp_object_type(details, details_before, object_type, "deactivate")
        logger.info(
            "_%s: deactivated=%d skipped=%d (of %d candidates)",
            f"deactivate_{object_type.replace('-', '_')}",
            deactivated_count,
            skipped_count,
            len(deactivate_source_ids),
        )
        self._record_phase_result(
            summary, object_type, "deactivate", deactivated=deactivated_count, skipped=skipped_count
        )
        self._save_run_log(summary)

    def _deactivate_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate TrafficSignReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["signs_deactivated"] and phase results are
                appended.
        """
        self._deactivate_objects(
            summary,
            rows_by_id=self.signs_by_id,
            source_id_to_db_id=self.sign_source_id_to_db_id,
            model_class=TrafficSignReal,
            object_type="signs",
            summary_key="signs_deactivated",
            object_type_name="TrafficSignReal",
        )

    # ------------------------------------------------------------------
    # Signpost handlers
    # ------------------------------------------------------------------

    def _create_signposts(self, summary: dict[str, Any]) -> None:
        """Create new SignpostReal records using a BFS multi-pass strategy.

        Each pass inserts signposts whose parent is already resolved (either
        pre-existing in the DB or created in a previous pass).  The loop
        repeats until all candidates are processed, naturally handling trees of
        arbitrary depth (e.g. Grandparent → Parent → Node → Leaf).  Candidates
        whose parent cannot be resolved after all resolvable nodes are drained
        are imported without a parent and a warning is recorded.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries
                are appended to summary["details"] and summary["signposts_created"]
                is incremented.
        """
        phase_started_at = datetime.datetime.now(tz=datetime.timezone.utc)
        summary.setdefault("signposts_created", 0)
        details_before = len(summary.get("details", []))

        # In-run map: source_id → db pk for signposts created so far this run.
        newly_created: dict[str, UUID] = {}

        existing_source_ids: KeysView[str] = self.signpost_source_id_to_db_id.keys()
        candidate_source_ids = [
            s
            for s, row in self.signposts_by_id.items()
            if s not in existing_source_ids and row.get(CSVHeadersV2.status) != "Removed"
        ]
        candidates_set: set[str] = set(candidate_source_ids)
        remaining: list[str] = candidate_source_ids
        created_count = 0

        while remaining:
            combined_parent_map = {**self.signpost_source_id_to_db_id, **newly_created}
            # Ready: no parent, parent already in DB/created, or parent is not a
            # candidate (unresolvable — will warn inside _run_signpost_pass).
            ready = [
                s
                for s in remaining
                if not self.signposts_by_id[s].get(CSVHeadersV2.parent_sign_id, "")
                or self.signposts_by_id[s].get(CSVHeadersV2.parent_sign_id, "") in combined_parent_map
                or self.signposts_by_id[s].get(CSVHeadersV2.parent_sign_id, "") not in candidates_set
            ]
            if not ready:
                # No progress possible (e.g. circular refs). Force all remaining
                # nodes through in one final pass: _run_signpost_pass will set
                # parent_id=None and record a warning for each unresolved parent.
                # After this pass, remaining becomes empty and the loop exits.
                ready = remaining
            remaining = [s for s in remaining if s not in set(ready)]
            created_count += self._run_signpost_pass(
                source_ids=ready,
                parent_map=combined_parent_map,
                newly_created=newly_created,
                summary=summary,
                phase_started_at=phase_started_at,
            )

        summary["signposts_created"] += created_count
        self._stamp_object_type(summary.setdefault("details", []), details_before, "signposts", "create")
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

    def _run_signpost_pass(
        self,
        source_ids: list[str],
        parent_map: dict[str, Any],
        newly_created: dict[str, UUID],
        summary: dict[str, Any],
        phase_started_at: datetime.datetime,
    ) -> int:
        """Insert one batch of signpost rows (either roots or children).

        Args:
            source_ids (list[str]): Ordered list of source IDs for this pass.
            parent_map (dict[str, Any]): Combined source_id → DB PK map covering
                pre-existing and previously-created signposts.
            newly_created (dict[str, UUID]): Mutable map updated with PKs created
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

            location = self._validate_and_get_location(row, source_id, details)
            if location is None:
                continue

            fields = self._resolve_signpost_create_fields(row, source_id, parent_map, details)
            if fields is None:
                continue

            processed.append(source_id)
            objects_to_create.append(
                SignpostReal(
                    source_id=source_id,
                    source_name=SOURCE_NAME,
                    location=location,
                    device_type_id=fields["device_type_id"],
                    owner=self.default_owner,
                    installation_status=InstallationStatus.IN_USE,
                    lifecycle=Lifecycle.ACTIVE,
                    parent_id=fields["parent_id"],
                    mount_real_id=fields["mount_real_id"],
                    mount_type=fields["mount_type"],
                    direction=fields["direction"],
                    height=fields["height"],
                    condition=fields["condition"],
                    location_specifier=fields["location_specifier"],
                    value=fields["value"],
                    txt=fields["txt"],
                    scanned_at=fields["scanned_at"],
                    attachment_url=fields["attachment_url"],
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

    def _prepare_signpost_for_update(
        self,
        obj: Any,
        row: dict[str, Any],
        source_id: str,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> bool:
        """Mutate a SignpostReal instance in-place with new CSV values.

        Args:
            obj (Any): Existing SignpostReal DB instance to mutate.
            row (dict[str, Any]): CSV row for this source_id.
            source_id (str): Source identifier used for error reporting.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``updated_at``.

        Returns:
            bool: True if the object was mutated and should be bulk-updated, False to skip.
        """
        fields = self._resolve_signpost_update_fields(row, source_id, details)
        if fields is None or not self._signpost_fields_changed(obj, fields):
            return False
        if not self.dry_run:
            self._create_signpost_update_revert_record(obj, source_id)
        obj.source_name = SOURCE_NAME
        obj.location = fields["location"]
        obj.device_type_id = fields["device_type_id"]
        obj.owner = self.default_owner
        obj.mount_real_id = fields["mount_real_id"]
        obj.mount_type = fields["mount_type"]
        obj.direction = fields["direction"]
        obj.height = fields["height"]
        obj.condition = fields["condition"]
        obj.location_specifier = fields["location_specifier"]
        obj.value = fields["value"]
        obj.txt = fields["txt"]
        obj.scanned_at = fields["scanned_at"]
        obj.attachment_url = fields["attachment_url"]
        obj.updated_by = self.user
        obj.updated_at = phase_started_at
        return True

    def _update_signposts(self, summary: dict[str, Any]) -> None:
        """Update existing SignpostReal records from non-Removed CSV rows.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["signposts_updated"] and phase results are appended.
        """
        self._update_objects(
            summary,
            rows_by_id=self.signposts_by_id,
            source_id_to_db_id=self.signpost_source_id_to_db_id,
            model_class=SignpostReal,
            object_type="signposts",
            summary_key="signposts_updated",
            update_fields=[
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
            ],
            prepare_row=self._prepare_signpost_for_update,
        )

    def _create_additional_sign_update_revert_record(self, obj: Any, source_id: str) -> None:
        """Create and write a revert record for an additional sign update operation.

        Args:
            obj (Any): Existing AdditionalSignReal DB instance being updated.
            source_id (str): Source identifier.
        """
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

    def _resolve_signpost_create_fields(
        self,
        row: dict,
        source_id: str,
        parent_map: dict[str, Any],
        details: list[dict],
    ) -> dict[str, Any] | None:
        """Resolve and validate all field values for a signpost create row.

        Validates device type code, resolves FK ids (mount, parent), and casts
        all field values. Returns ``None`` and appends a skip entry when a hard
        validation error is encountered. Mount/parent resolution warnings are
        appended but do not cause a skip.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier.
            parent_map (dict[str, Any]): Map of parent source_ids to DB PKs.
            details (list[dict]): Mutable details list for skip/warning entries.

        Returns:
            dict[str, Any] | None: Resolved field dict, or None if row must be skipped.
        """
        device_type_id = self._resolve_device_type_id(row, source_id, details)
        if device_type_id is None:
            return None

        # Mount resolution — warn but still import without mount.
        mount_real_id = self._resolve_mount_real_id(row, source_id, details)

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
        value = self._get_sign_value(number_code_str, source_id, details)

        return {
            "device_type_id": device_type_id,
            "mount_real_id": mount_real_id,
            "mount_type": mount_type,
            "parent_id": parent_id,
            "location_specifier": location_specifier,
            "value": value,
            "direction": self._get_sign_direction(row.get(CSVHeadersV2.direction), source_id, details),
            "height": self._get_sign_height(row.get(CSVHeadersV2.height), source_id, details),
            "condition": self._get_sign_condition(row.get(CSVHeadersV2.condition), source_id, details),
            "txt": row.get(CSVHeadersV2.txt, "") or None,
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.scanned_at), source_id, details),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
        }

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
        new_location = self._validate_and_get_location(row, source_id, details, _ON_UPDATE_SUFFIX)
        if new_location is None:
            return None

        device_type_id = self._resolve_device_type_id(row, source_id, details)
        if device_type_id is None:
            return None

        new_mount_real_id = self._resolve_mount_real_id(row, source_id, details)

        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        return {
            "location": new_location,
            "device_type_id": device_type_id,
            "mount_real_id": new_mount_real_id,
            "mount_type": self.mount_types_by_name.get(row.get(CSVHeadersV2.sign_mount_type, "")),
            "location_specifier": SignLocationSpecifier(int(raw_ls)) if raw_ls else None,
            "value": self._get_sign_value(row.get(CSVHeadersV2.number_code, "") or "", source_id, details),
            "height": self._get_sign_height(row.get(CSVHeadersV2.height), source_id, details),
            "direction": self._get_sign_direction(row.get(CSVHeadersV2.direction), source_id, details),
            "condition": self._get_sign_condition(row.get(CSVHeadersV2.condition), source_id, details),
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.scanned_at), source_id, details),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
            "txt": row.get(CSVHeadersV2.txt, "") or None,
        }

    def _signpost_fields_changed(
        self,
        obj: Any,
        fields: dict[str, Any],
    ) -> bool:
        """Return True if any signpost field differs from the stored DB values.

        Args:
            obj (Any): Existing SignpostReal DB instance.
            fields (dict[str, Any]): Dictionary containing new field values returned
                by _resolve_signpost_update_fields.

        Returns:
            bool: True if any field has changed or force_update is set.
        """
        if self.force_update:
            return True

        new_mount_type = fields["mount_type"]
        comparisons: list[tuple[Any, Any]] = [
            (obj.source_name, SOURCE_NAME),
            (obj.location, fields["location"]),
            (obj.device_type_id, fields["device_type_id"]),
            (obj.mount_real_id, fields["mount_real_id"]),
            (obj.mount_type_id, new_mount_type.pk if new_mount_type else None),
            (obj.direction, fields["direction"]),
            (obj.height, fields["height"]),
            (obj.condition, fields["condition"]),
            (obj.location_specifier, fields["location_specifier"]),
            (obj.value, fields["value"]),
            (obj.txt, fields["txt"]),
            (obj.scanned_at, fields["scanned_at"]),
            (obj.attachment_url, fields["attachment_url"]),
        ]
        return any(old != new for old, new in comparisons)

    def _create_signpost_update_revert_record(self, obj: Any, source_id: str) -> None:
        """Create and write a revert record for a signpost update operation.

        Args:
            obj (Any): Existing SignpostReal DB instance being updated.
            source_id (str): Source identifier.
        """
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

    def _deactivate_signposts(self, summary: dict[str, Any]) -> None:
        """Deactivate SignpostReal records whose CSV status is ``Removed``.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["signposts_deactivated"] and phase results
                are appended.
        """
        self._deactivate_objects(
            summary,
            rows_by_id=self.signposts_by_id,
            source_id_to_db_id=self.signpost_source_id_to_db_id,
            model_class=SignpostReal,
            object_type="signposts",
            summary_key="signposts_deactivated",
            object_type_name="SignpostReal",
        )

    # ------------------------------------------------------------------
    # Additional sign handlers (skeleton)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Additional sign field helpers
    # ------------------------------------------------------------------

    def _get_additional_sign_color(self, color_str: str | None, source_id: str, details: list[dict]) -> Color | None:
        """Parse the color field into a Color enum value.

        Args:
            color_str (str | None): Raw color string from CSV, or None.
            source_id (str): Source identifier used for warning messages.
            details (list[dict]): Mutable details list; a warning is appended on parse failure.

        Returns:
            Color | None: Parsed Color enum value, or None if absent/invalid.
        """
        if not color_str:
            details.append({"level": "warning", "source_id": source_id, "reason": "color is absent or empty"})
            return None
        try:
            value = int(color_str)
            return Color(value) if value else None
        except (ValueError, TypeError):
            details.append(
                {"level": "warning", "source_id": source_id, "reason": f"Could not parse color={color_str!r}"}
            )
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
        signpost_pk = self.signpost_source_id_to_db_id.get(parent_csv_id)

        if traffic_sign_pk is None and signpost_pk is None:
            details.append(
                {
                    "level": "warning",
                    "source_id": source_id,
                    "reason": f"Parent sign not found in signs or signposts for parent CSV id: {parent_csv_id}",
                }
            )

        return traffic_sign_pk, (signpost_pk if traffic_sign_pk is None else None)

    def _resolve_additional_sign_fields(
        self,
        row: dict,
        source_id: str,
        details: list[dict],
    ) -> dict[str, Any] | None:
        """Resolve and validate all field values for an additional sign create or update row.

        Validates text (skips "unreadable"), device type code, resolves FK ids
        (mount, parent), and casts all field values. Returns ``None`` and appends a
        skip entry when a hard validation error is encountered.

        Args:
            row (dict): CSV row data.
            source_id (str): Source identifier.
            details (list[dict]): Mutable details list for skip/warning entries.

        Returns:
            dict[str, Any] | None: Resolved field dict, or None if row must be skipped.
        """
        txt = row.get(CSVHeadersV2.txt, "") or ""
        if txt.strip().lower() == "unreadable":
            details.append({"level": "skip", "source_id": source_id, "reason": "text value is unreadable"})
            return None

        device_type_id = self._resolve_device_type_id(row, source_id, details)
        if device_type_id is None:
            return None

        mount_real_id = self._resolve_mount_real_id(row, source_id, details)

        parent_csv_id = row.get(CSVHeadersV2.parent_sign_id, "")
        parent_id, signpost_real_id = self._resolve_additional_sign_parent(parent_csv_id, source_id, details)

        number_code_str = row.get(CSVHeadersV2.number_code, "") or ""
        raw_ls = row.get(CSVHeadersV2.location_specifier, "")
        location_specifier = SignLocationSpecifier(int(raw_ls)) if raw_ls else None
        mount_type = self.mount_types_by_name.get(row.get(CSVHeadersV2.sign_mount_type, ""))
        internal_info = row.get("internal_additional_info")

        return {
            "device_type_id": device_type_id,
            "parent_id": parent_id,
            "signpost_real_id": signpost_real_id,
            "mount_real_id": mount_real_id,
            "mount_type": mount_type,
            "location_specifier": location_specifier,
            "color": self._get_additional_sign_color(row.get(CSVHeadersV2.color), source_id, details),
            "additional_information": self._build_additional_information(txt, number_code_str, internal_info),
            "direction": self._get_sign_direction(row.get(CSVHeadersV2.direction), source_id, details),
            "height": self._get_sign_height(row.get(CSVHeadersV2.height), source_id, details),
            "condition": self._get_sign_condition(row.get(CSVHeadersV2.condition), source_id, details),
            "scanned_at": self._get_scanned_at(row.get(CSVHeadersV2.scanned_at), source_id, details),
            "attachment_url": row.get(CSVHeadersV2.attachment_url, ""),
        }

    def _additional_sign_fields_changed(
        self,
        obj: Any,
        new_location: Any,
        fields: dict[str, Any],
    ) -> bool:
        """Check if any additional sign fields have changed from stored DB values.

        Args:
            obj (Any): Existing AdditionalSignReal DB instance.
            new_location (Any): New geometry point.
            fields (dict[str, Any]): Dictionary containing new field values.

        Returns:
            bool: True if any field has changed or force_update is set.
        """
        if self.force_update:
            return True

        new_mount_type = fields["mount_type"]
        comparisons: list[tuple[Any, Any]] = [
            (obj.source_name, SOURCE_NAME),
            (obj.location, new_location),
            (obj.device_type_id, fields["device_type_id"]),
            (obj.parent_id, fields["parent_id"]),
            (obj.signpost_real_id, fields["signpost_real_id"]),
            (obj.mount_real_id, fields["mount_real_id"]),
            (obj.mount_type_id, new_mount_type.pk if new_mount_type else None),
            (obj.direction, fields["direction"]),
            (obj.height, fields["height"]),
            (obj.condition, fields["condition"]),
            (obj.location_specifier, fields["location_specifier"]),
            (obj.color, fields["color"]),
            (obj.additional_information, fields["additional_information"]),
            (obj.scanned_at, fields["scanned_at"]),
            (obj.attachment_url, fields["attachment_url"]),
        ]
        return any(old != new for old, new in comparisons)

    # ------------------------------------------------------------------
    # Additional sign phase handlers
    # ------------------------------------------------------------------

    def _build_additional_sign_for_create(
        self,
        source_id: str,
        row: dict[str, Any],
        location: Any,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> AdditionalSignReal | None:
        """Build an unsaved AdditionalSignReal instance from a CSV row.

        Args:
            source_id (str): Source identifier.
            row (dict[str, Any]): CSV row for this source_id.
            location (Any): Already-validated geometry point.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``created_at``.

        Returns:
            AdditionalSignReal | None: Unsaved instance, or None if row must be skipped.
        """
        fields = self._resolve_additional_sign_fields(row, source_id, details)
        if fields is None:
            return None
        return AdditionalSignReal(
            source_id=source_id,
            source_name=SOURCE_NAME,
            location=location,
            device_type_id=fields["device_type_id"],
            owner=self.default_owner,
            installation_status=InstallationStatus.IN_USE,
            lifecycle=Lifecycle.ACTIVE,
            missing_content=True,
            parent_id=fields["parent_id"],
            signpost_real_id=fields["signpost_real_id"],
            mount_real_id=fields["mount_real_id"],
            mount_type=fields["mount_type"],
            direction=fields["direction"],
            height=fields["height"],
            condition=fields["condition"],
            location_specifier=fields["location_specifier"],
            color=fields["color"],
            additional_information=fields["additional_information"],
            scanned_at=fields["scanned_at"],
            attachment_url=fields["attachment_url"],
            created_by=self.user,
            created_at=phase_started_at,
        )

    def _create_additional_signs(self, summary: dict[str, Any]) -> None:
        """Create new AdditionalSignReal records from CSV rows not yet in the DB.

        Args:
            summary (dict[str, Any]): Mutable summary dict; skip/warning entries
                are appended to summary["details"] and
                summary["additional_signs_created"] is incremented.
        """
        self._create_objects(
            summary,
            rows_by_id=self.additional_signs_by_id,
            existing_source_ids=self.additional_sign_source_id_to_db_id.keys(),
            model_class=AdditionalSignReal,
            object_type="additional-signs",
            summary_key="additional_signs_created",
            object_type_name="AdditionalSignReal",
            processed_key="processed_additional_sign_source_ids",
            build_object=self._build_additional_sign_for_create,
        )

    def _prepare_additional_sign_for_update(
        self,
        obj: Any,
        row: dict[str, Any],
        source_id: str,
        details: list[dict],
        phase_started_at: datetime.datetime,
    ) -> bool:
        """Mutate an AdditionalSignReal instance in-place with new CSV values.

        Args:
            obj (Any): Existing AdditionalSignReal DB instance to mutate.
            row (dict[str, Any]): CSV row for this source_id.
            source_id (str): Source identifier used for error reporting.
            details (list[dict]): Mutable details list for skip/warning entries.
            phase_started_at (datetime.datetime): Timestamp used as ``updated_at``.

        Returns:
            bool: True if the object was mutated and should be bulk-updated, False to skip.
        """
        new_location = self._validate_and_get_location(row, source_id, details, _ON_UPDATE_SUFFIX)
        fields = self._resolve_additional_sign_fields(row, source_id, details)
        fields_unchanged = fields is not None and not self._additional_sign_fields_changed(obj, new_location, fields)
        if new_location is None or fields is None or fields_unchanged:
            return False
        if not self.dry_run:
            self._create_additional_sign_update_revert_record(obj, source_id)
        obj.source_name = SOURCE_NAME
        obj.location = new_location
        obj.device_type_id = fields["device_type_id"]
        obj.owner = self.default_owner
        obj.parent_id = fields["parent_id"]
        obj.signpost_real_id = fields["signpost_real_id"]
        obj.mount_real_id = fields["mount_real_id"]
        obj.mount_type = fields["mount_type"]
        obj.direction = fields["direction"]
        obj.height = fields["height"]
        obj.condition = fields["condition"]
        obj.location_specifier = fields["location_specifier"]
        obj.color = fields["color"]
        obj.additional_information = fields["additional_information"]
        obj.scanned_at = fields["scanned_at"]
        obj.attachment_url = fields["attachment_url"]
        obj.updated_by = self.user
        obj.updated_at = phase_started_at
        return True

    def _update_additional_signs(self, summary: dict[str, Any]) -> None:
        """Update existing AdditionalSignReal records from non-Removed CSV rows.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the updated count is
                recorded in summary["additional_signs_updated"] and phase results
                are appended.
        """
        self._update_objects(
            summary,
            rows_by_id=self.additional_signs_by_id,
            source_id_to_db_id=self.additional_sign_source_id_to_db_id,
            model_class=AdditionalSignReal,
            object_type="additional-signs",
            summary_key="additional_signs_updated",
            update_fields=[
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
            ],
            prepare_row=self._prepare_additional_sign_for_update,
        )

    def _deactivate_additional_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate AdditionalSignReal records whose CSV status is ``Removed``.

        Args:
            summary (dict[str, Any]): Mutable summary dict; the deactivated count
                is recorded in summary["additional_signs_deactivated"] and phase
                results are appended.
        """
        self._deactivate_objects(
            summary,
            rows_by_id=self.additional_signs_by_id,
            source_id_to_db_id=self.additional_sign_source_id_to_db_id,
            model_class=AdditionalSignReal,
            object_type="additional-signs",
            summary_key="additional_signs_deactivated",
            object_type_name="AdditionalSignReal",
        )
