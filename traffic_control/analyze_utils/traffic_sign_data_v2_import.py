"""V2 traffic sign importer.

Handles create, update and deactivate operations for MountReal, TrafficSignReal,
SignpostReal and AdditionalSignReal based on enriched V2 CSV data.

This module is intentionally kept separate from the analysis pipeline so that
the management command can run an import without triggering the full analysis.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from traffic_control.analyze_utils.traffic_sign_data_v2_code_transform import CodeTransformMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_data_loading import DataLoadingMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_db_builders import DbBuilderMixin

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
        phases (list[str]): Operation phases to run. Must be a subset of
            VALID_PHASES.
        dry_run (bool): When True, no DB writes are performed.
        resume (bool): When True, source_ids already recorded in previous run
            logs for the same file pair are skipped.
        delimiter (str): CSV delimiter character.
    """

    def __init__(
        self,
        mount_file: str,
        sign_file: str,
        object_types: list[str],
        phases: list[str],
        dry_run: bool = False,
        resume: bool = False,
        delimiter: str = ",",
    ) -> None:
        """Initialise the importer: load CSV rows, enrich them and build DB lookup maps.

        Args:
            mount_file (str): Path to the mount CSV file.
            sign_file (str): Path to the sign CSV file.
            object_types (list[str]): Object types to process.
            phases (list[str]): Operation phases to run.
            dry_run (bool): If True, no DB writes are performed.
            resume (bool): If True, skip already-processed source_ids.
            delimiter (str): CSV delimiter character.
        """
        self.mount_file = mount_file
        self.sign_file = sign_file
        self.dry_run = dry_run
        self.resume = resume
        self.delimiter = delimiter

        # Normalise and sort by dependency order.
        self.object_types: list[str] = [ot for ot in OBJECT_TYPE_ORDER if ot in object_types]
        self.phases: list[str] = list(phases)

        # --- CSV loading ---
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

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """Execute the import for the configured object types and phases.

        Returns:
            dict[str, Any]: Summary dict with counts and details entries
                collected during the run.
        """
        print("[TrafficSignImporterV2] Starting import")
        print(f"  mount_file   : {self.mount_file}")
        print(f"  sign_file    : {self.sign_file}")
        print(f"  object_types : {self.object_types}")
        print(f"  phases       : {self.phases}")
        print(f"  dry_run      : {self.dry_run}")
        print(f"  resume       : {self.resume}")
        print(f"  mount rows   : {len(self.mount_rows)}")
        print(f"  sign rows (enriched): {len(self.sign_rows)}")
        print(f"  signs        : {len(self.signs_by_id)}")
        print(f"  additional signs: {len(self.additional_signs_by_id)}")
        print(f"  signposts    : {len(self.signposts_by_id)}")

        summary: dict[str, Any] = {
            "object_types": self.object_types,
            "phases": self.phases,
            "dry_run": self.dry_run,
            "details": [],
        }

        for object_type in self.object_types:
            self._run_object_type(object_type, summary)

        print("[TrafficSignImporterV2] Import finished")
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
        print(f"\n[TrafficSignImporterV2] Object type: {object_type}")
        for phase in self.phases:
            if phase == "deactivate" and object_type not in _DEACTIVATABLE_OBJECT_TYPES:
                print(f"  Skipping phase '{phase}' — {object_type} are never deactivated")
                continue
            self._run_phase(object_type, phase, summary)

    def _run_phase(self, object_type: str, phase: str, summary: dict[str, Any]) -> None:
        """Dispatch a single object-type / phase combination.

        Args:
            object_type (str): One of VALID_OBJECT_TYPES.
            phase (str): One of VALID_PHASES.
            summary (dict[str, Any]): Mutable summary dict to update with results.
        """
        print(f"  Phase: {phase}")
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
            print(f"    [WARN] No handler for ({object_type}, {phase}) — skipping")
            return
        handler(summary)

    # ------------------------------------------------------------------
    # Mount handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_mounts(self, summary: dict[str, Any]) -> None:
        """Create new MountReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _create_mounts — {len(self.mounts_by_id)} rows available")

    def _update_mounts(self, summary: dict[str, Any]) -> None:
        """Update existing MountReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _update_mounts — {len(self.mount_source_id_to_db_id)} existing in DB")

    # ------------------------------------------------------------------
    # Traffic sign handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_signs(self, summary: dict[str, Any]) -> None:
        """Create new TrafficSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _create_signs — {len(self.signs_by_id)} rows available")

    def _update_signs(self, summary: dict[str, Any]) -> None:
        """Update existing TrafficSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _update_signs — {len(self.sign_source_id_to_db_id)} existing in DB")

    def _deactivate_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate TrafficSignReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _deactivate_signs — {len(self.sign_reals_by_source_id)} known in DB")

    # ------------------------------------------------------------------
    # Signpost handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_signposts(self, summary: dict[str, Any]) -> None:
        """Create new SignpostReal records (two-pass for parent ordering).

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _create_signposts — {len(self.signposts_by_id)} rows available")

    def _update_signposts(self, summary: dict[str, Any]) -> None:
        """Update existing SignpostReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _update_signposts — {len(self.signpost_source_id_to_db_id)} existing in DB")

    def _deactivate_signposts(self, summary: dict[str, Any]) -> None:
        """Deactivate SignpostReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _deactivate_signposts — {len(self.signpost_reals_by_source_id)} known in DB")

    # ------------------------------------------------------------------
    # Additional sign handlers (skeleton)
    # ------------------------------------------------------------------

    def _create_additional_signs(self, summary: dict[str, Any]) -> None:
        """Create new AdditionalSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _create_additional_signs — {len(self.additional_signs_by_id)} rows available")

    def _update_additional_signs(self, summary: dict[str, Any]) -> None:
        """Update existing AdditionalSignReal records.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _update_additional_signs — {len(self.additional_sign_source_id_to_db_id)} existing in DB")

    def _deactivate_additional_signs(self, summary: dict[str, Any]) -> None:
        """Deactivate AdditionalSignReal records marked as Removed in CSV.

        Args:
            summary (dict[str, Any]): Mutable summary dict.
        """
        print(f"    [TODO] _deactivate_additional_signs — {len(self.additional_sign_reals_by_source_id)} known in DB")
