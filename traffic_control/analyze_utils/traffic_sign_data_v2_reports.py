"""Analysis report methods mixin for TrafficSignAnalyzerV2."""
from typing import Any

from django.contrib.gis.geos import Point

from traffic_control.geometry_utils import geometry_is_legit

from .traffic_sign_data_v2_constants import (
    CSVHeadersV2,
    DIRECTION_TOLERANCE,
    DUPLICATE_PAIR_EXCLUDED_CODES,
    ZEBRA_CROSSING_ALL_CODES,
)


class ReportsMixin:
    """Mixin providing existing analysis, duplicate detection, sanity check and location distance reports."""

    # ==================== Existing Analysis Reports ====================

    def _get_non_existing_mounts_for_signs(self):
        """Report signs with non-existing mount references."""
        results = []
        for sign_id, mount_id in self.no_mounts_per_sign_id.items():
            sign_data = self.signs_by_id.get(sign_id, {})
            mount_data = self.mounts_by_id.get(mount_id, {})
            results.append(
                {
                    "sign_source_id": sign_id,
                    "mount_source_id": mount_id,
                    "devicetypecode": sign_data.get(CSVHeadersV2.code, ""),
                    "status": sign_data.get(CSVHeadersV2.status, ""),
                    "internal_status": sign_data.get("internal_status", ""),
                    "csv_ssurl": sign_data.get(CSVHeadersV2.attachment_url, ""),
                    "mount_ssurl": mount_data.get(CSVHeadersV2.attachment_url, ""),
                }
            )
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS", "results": results}

    def _get_non_existing_mounts_for_additional_signs(self):
        """Report additional signs with non-existing mount references."""
        results = []
        for sign_id, mount_id in self.no_mounts_per_additional_sign_id.items():
            sign_data = self.additional_signs_by_id.get(sign_id, {})
            mount_data = self.mounts_by_id.get(mount_id, {})
            results.append(
                {
                    "additional_sign_source_id": sign_id,
                    "mount_source_id": mount_id,
                    "devicetypecode": sign_data.get(CSVHeadersV2.code, ""),
                    "status": sign_data.get(CSVHeadersV2.status, ""),
                    "internal_status": sign_data.get("internal_status", ""),
                    "additional_sign_ssurl": sign_data.get(CSVHeadersV2.attachment_url, ""),
                    "mount_ssurl": mount_data.get(CSVHeadersV2.attachment_url, ""),
                }
            )
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS", "results": results}

    def _get_mount_distances(self):
        """Report distances from mounts to attached signs."""
        results = []
        for mount_id, data_d in self.mounts_by_id.items():
            distances = {
                "additional_signs": self._get_distances_for_mount(data_d, "additional_signs"),
                "signs": self._get_distances_for_mount(data_d, "signs"),
            }
            results.append({"mount_source_id": mount_id, "distance": distances})
        return {"REPORT_TYPE": "MOUNT DISTANCES", "results": results}

    @staticmethod
    def _get_distances_for_mount(mount_data, objects_field_name):
        """Helper to calculate distances for mount."""
        distances = {}
        for entry in mount_data[objects_field_name]:
            distances.setdefault(entry[CSVHeadersV2.id], []).append(entry["distance_to_mount"])
        return [{"mount_source_id": mount_data[CSVHeadersV2.id], "distances": distances}]

    def _get_sign_distances(self):
        """Report distances from signs to mounts."""
        results = [
            {
                "sign_source_id": x.get(CSVHeadersV2.id),
                "sign_code": x.get(CSVHeadersV2.code),
                "mount_source_id": x.get(CSVHeadersV2.mount_id),
                "mount_type": self._get_mount_type(x.get(CSVHeadersV2.mount_id)),
                "distance_to_mount": x.get("distance_to_mount"),
                "status": x.get(CSVHeadersV2.status),
                "link": x.get(CSVHeadersV2.attachment_url),
            }
            for x in self.signs_by_id.values()
            if x.get(CSVHeadersV2.id) not in self.no_mounts_per_sign_id
        ]
        return {"REPORT_TYPE": "SIGN DISTANCES", "results": results}

    def _get_additional_sign_distances(self):
        """Report distances from additional signs to mounts and parent signs."""
        results = [
            {
                "additional_sign_source_id": x.get(CSVHeadersV2.id),
                "sign_code": x.get(CSVHeadersV2.code),
                "mount_source_id": x.get(CSVHeadersV2.mount_id),
                "mount_type": self._get_mount_type(x.get(CSVHeadersV2.mount_id)),
                "distance_to_mount": x.get("distance_to_mount"),
                "parent_source_id": x.get(CSVHeadersV2.parent_sign_id),
                "distance_to_parent": x.get("distance_to_parent"),
                "parent_is_additional_sign": x.get("parent_is_additional_sign"),
                "parent_code": x.get("parent_code"),
                "status": x.get(CSVHeadersV2.status),
                "link": x.get(CSVHeadersV2.attachment_url),
            }
            for x in self.additional_signs_by_id.values()
            if x.get(CSVHeadersV2.id) not in self.no_mounts_per_additional_sign_id
        ]
        return {"REPORT_TYPE": "ADDITIONAL SIGN DISTANCES", "results": results}

    def _is_mountless(self, mount_id: str) -> bool:
        """Check whether a mount_id is considered mountless.

        A sign is considered mountless if its mount_id is blank, the mount does not exist
        in the mounts CSV, or the referenced mount has status Removed.

        Args:
            mount_id (str): The mount source ID from the sign row.

        Returns:
            bool: True if the sign should be considered mountless.
        """
        if not mount_id:
            return True
        mount_data = self.mounts_by_id.get(mount_id)
        return mount_data is None or mount_data.get(CSVHeadersV2.status) == "Removed"

    def _build_mountless_report(self, objects: dict, report_type: str, id_key: str) -> dict[str, Any]:
        """Build a mountless report for any object type.

        Args:
            objects (dict): Mapping of source_id to CSV row data.
            report_type (str): REPORT_TYPE label string for the result dict.
            id_key (str): Result dict key to use for the source_id value.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result entry contains id_key, status, mount_status, object_ssurl,
                mount_ssurl (empty string if mount not found), devicetype_code, and
                mount_type (empty string if mount not found).
        """
        results = []
        for x in objects.values():
            if x.get(CSVHeadersV2.status) == "Removed" or not self._is_mountless(x[CSVHeadersV2.mount_id]):
                continue
            mount_data = self.mounts_by_id.get(x[CSVHeadersV2.mount_id])
            mount_status = mount_data.get(CSVHeadersV2.status) if mount_data else "does not exist"
            mount_id = mount_data.get(CSVHeadersV2.id) if mount_data else "does not exist"
            mount_ssurl = mount_data.get(CSVHeadersV2.attachment_url, "") if mount_data else ""
            mount_type = mount_data.get(CSVHeadersV2.mount_type, "") if mount_data else ""
            results.append(
                {
                    id_key: x.get(CSVHeadersV2.id),
                    "status": x.get(CSVHeadersV2.status),
                    "mount_id": mount_id,
                    "mount_status": mount_status,
                    "object_ssurl": x.get(CSVHeadersV2.attachment_url, ""),
                    "mount_ssurl": mount_ssurl,
                    "devicetype_code": x.get(CSVHeadersV2.code, ""),
                    "mount_type": mount_type,
                }
            )
        return {"REPORT_TYPE": report_type, "results": results}

    def _get_mountless_signs(self) -> dict[str, Any]:
        """Report signs without valid mount references."""
        return self._build_mountless_report(self.signs_by_id, "MOUNTLESS SIGNS", "sign_source_id")

    def _get_mountless_additional_signs(self) -> dict[str, Any]:
        """Report additional signs without valid mount references."""
        return self._build_mountless_report(
            self.additional_signs_by_id, "MOUNTLESS ADDITIONAL SIGNS", "additional_sign_source_id"
        )

    def _get_mountless_signposts(self) -> dict[str, Any]:
        """Report signposts without valid mount references."""
        return self._build_mountless_report(self.signposts_by_id, "MOUNTLESS SIGNPOSTS", "signpost_source_id")

    def _get_signless_additional_signs(self):
        """Report additional signs without parent sign references.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for obj in filter(lambda x: not x[CSVHeadersV2.parent_sign_id], self.additional_signs_by_id.values()):
            source_id = obj.get(CSVHeadersV2.id)
            results.append(
                {
                    "additional_sign_source_id": source_id,
                    "old_device_code": self.additional_sign_reals_by_source_id.get(source_id),
                    "new_device_code": obj.get(CSVHeadersV2.code),
                    "status": obj.get(CSVHeadersV2.status),
                    "internal_status": obj.get("internal_status", ""),
                    "csv_ssurl": obj.get(CSVHeadersV2.attachment_url, ""),
                }
            )
        return {"REPORT_TYPE": "SIGNLESS ADDITIONAL SIGNS", "results": results}

    def _get_mount_type(self, mount_id):
        """Get mount type for a given mount ID."""
        mount = self.mounts_by_id.get(mount_id)
        return mount.get(CSVHeadersV2.mount_type) if mount else None

    # ==================== CSV Preprocessing Reports ====================

    def _get_filtered_signs_report(self) -> dict[str, Any]:
        """Report sign rows that were filtered out during CSV reading.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {"REPORT_TYPE": "FILTERED SIGNS (REMOVED FROM CSV)", "results": self.filtered_signs}

    def _get_enriched_signs_report(self) -> dict[str, Any]:
        """Report sign rows that had location_specifier values added.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {"REPORT_TYPE": "ENRICHED SIGNS (LOCATION_SPECIFIER ADDED)", "results": self.enriched_signs}

    def _get_code_replacements_report(self) -> dict[str, Any]:
        """Report sign rows that had device type codes replaced.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {"REPORT_TYPE": "CODE REPLACEMENTS (DEVICE TYPE CODES UPDATED)", "results": self.code_replacements}

    def _get_code_replacement_failures_report(self) -> dict[str, Any]:
        """Report sign rows where code replacement failed sanity checks.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {
            "REPORT_TYPE": "CODE REPLACEMENT FAILURES (SANITY CHECK FAILURES)",
            "results": self.code_replacement_failures,
        }

    # ==================== Duplicate Detection Reports ====================

    def _get_duplicate_group_key(self, code: str, exact_code_match: bool) -> str | None:
        """Resolve the grouping key for a sign code when detecting duplicates.

        Args:
            code (str): The sign device code from the CSV row.
            exact_code_match (bool): If True, use the raw code; if False, use the device type ID.

        Returns:
            str | None: The grouping key, or None if the code has no matching device type.
        """
        if not code or code not in self.code_to_device_type_id:
            return None
        return code if exact_code_match else self.code_to_device_type_id.get(code)

    def _get_mount_location_ewkt(self, mount_id: str) -> str | None:
        """Return the EWKT representation of a mount's location.

        Args:
            mount_id (str): Source ID of the mount.

        Returns:
            str | None: EWKT string of the mount location, or None if not found.
        """
        mount_data = self.mounts_by_id.get(mount_id)
        if not mount_data:
            return None
        location = self._georeferenced_point_from_csv_row(mount_data)
        return location.ewkt

    @staticmethod
    def _format_duplicate_signs(sign_list: list[dict]) -> list[str]:
        """Format a list of sign dicts into human-readable duplicate sign strings.

        Args:
            sign_list (list[dict]): List of CSV sign row dicts.

        Returns:
            list[str]: Each entry formatted as "source_id | device_code | status | direction".
        """
        return [
            (
                f"{sign.get(CSVHeadersV2.id)} | {sign.get(CSVHeadersV2.code)}"
                f" | {sign.get(CSVHeadersV2.status)} | {sign.get(CSVHeadersV2.direction)}"
            )
            for sign in sign_list
        ]

    def _group_signs_by_key(self, signs: list[dict], exact_code_match: bool) -> dict[str, list[dict]]:
        """Group signs by device type key for duplicate detection.

        Args:
            signs (list[dict]): List of CSV sign row dicts for a single mount.
            exact_code_match (bool): If True, group by exact code; if False, by device type ID.

        Returns:
            dict[str, list[dict]]: Mapping of grouping key to list of matching sign dicts.
        """
        grouped: dict[str, list[dict]] = {}
        for sign in signs:
            if sign.get(CSVHeadersV2.status) == "Removed":
                continue
            key = self._get_duplicate_group_key(sign.get(CSVHeadersV2.code), exact_code_match)
            if key is not None:
                grouped.setdefault(key, []).append(sign)
        return grouped

    @staticmethod
    def _is_excluded_duplicate_pair(sign_list: list[dict]) -> bool:
        """Check whether a duplicate group should be excluded from the report.

        A group is excluded when it contains exactly 2 signs and every sign's
        device code belongs to ``DUPLICATE_PAIR_EXCLUDED_CODES`` (e.g. double-sided
        signs that legitimately appear in pairs on the same mount).

        Args:
            sign_list (list[dict]): List of CSV sign row dicts forming a duplicate group.

        Returns:
            bool: True if the group should be excluded from the report.
        """
        if len(sign_list) != 2:
            return False
        codes = [sign.get(CSVHeadersV2.code) for sign in sign_list]
        return codes[0] == codes[1] and codes[0] in DUPLICATE_PAIR_EXCLUDED_CODES

    def _get_duplicate_signs_on_same_mount(self, exact_code_match: bool = False) -> dict[str, Any]:
        """Report multiple signs on same mount with same device type or exact code.

        Args:
            exact_code_match (bool): If True, only match signs with exact same code.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for mount_id, signs in self.signs_by_mount_id.items():
            mount_data = self.mounts_by_id.get(mount_id)
            if mount_data and mount_data.get(CSVHeadersV2.status) == "Removed":
                continue
            grouped = self._group_signs_by_key(signs, exact_code_match)
            for sign_list in grouped.values():
                if len(sign_list) >= 2 and not self._is_excluded_duplicate_pair(sign_list):
                    results.append(
                        {
                            "mount_source_id": mount_id,
                            "mount_location": self._get_mount_location_ewkt(mount_id),
                            "duplicate_signs": self._format_duplicate_signs(sign_list),
                        }
                    )
        report_type = (
            "DUPLICATE SIGNS ON SAME MOUNT (EXACT CODE)" if exact_code_match else "DUPLICATE SIGNS ON SAME MOUNT"
        )
        return {"REPORT_TYPE": report_type, "results": results}

    def _get_duplicate_signs_on_same_mount_by_device_type(self) -> dict[str, Any]:
        """Report duplicates by device type (considering legacy codes).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_duplicate_signs_on_same_mount(exact_code_match=False)

    def _get_duplicate_signs_on_same_mount_exact_code(self) -> dict[str, Any]:
        """Report duplicates with exact same code.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_duplicate_signs_on_same_mount(exact_code_match=True)

    @staticmethod
    def _is_opposing_direction(sign1: dict, sign2: dict) -> tuple[bool, int, int, int]:
        """Check whether two signs face approximately opposite directions (180° apart).

        Args:
            sign1 (dict): First CSV sign row dict.
            sign2 (dict): Second CSV sign row dict.

        Returns:
            tuple[bool, int, int, int]: (is_opposing, dir1, dir2, diff).
        """
        try:
            dir1 = int(sign1.get(CSVHeadersV2.direction, 0))
            dir2 = int(sign2.get(CSVHeadersV2.direction, 0))
        except (ValueError, TypeError):
            return False, 0, 0, 0
        diff = abs(dir1 - dir2)
        if diff > 180:
            diff = 360 - diff
        return abs(diff - 180) <= DIRECTION_TOLERANCE, dir1, dir2, diff

    def _collect_zebra_pairs(self, mount_id: str, zebra_signs: list[dict]) -> list[dict[str, Any]]:
        """Find all opposing-direction zebra crossing pairs on a single mount.

        Args:
            mount_id (str): Source ID of the mount being examined.
            zebra_signs (list[dict]): Filtered list of New-status zebra crossing sign dicts.

        Returns:
            list[dict[str, Any]]: List of result dicts for each opposing pair found.
        """
        pairs = []
        for i, sign1 in enumerate(zebra_signs):
            for sign2 in zebra_signs[i + 1 :]:
                is_opposing, dir1, dir2, diff = self._is_opposing_direction(sign1, sign2)
                if is_opposing:
                    pairs.append(
                        {
                            "mount_source_id": mount_id,
                            "sign_source_ids": [sign1.get(CSVHeadersV2.id), sign2.get(CSVHeadersV2.id)],
                            "codes_found": [sign1.get(CSVHeadersV2.code), sign2.get(CSVHeadersV2.code)],
                            "directions": [dir1, dir2],
                            "direction_difference": diff,
                            "status": "New",
                        }
                    )
        return pairs

    def _get_added_double_sided_zebra_crossings(self) -> dict[str, Any]:
        """Report new zebra crossing signs that are double-sided (180° apart).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for mount_id, signs in self.signs_by_mount_id.items():
            zebra_signs = [
                sign
                for sign in signs
                if sign.get(CSVHeadersV2.status) == "New" and sign.get(CSVHeadersV2.code) in ZEBRA_CROSSING_ALL_CODES
            ]
            if len(zebra_signs) >= 2:
                results.extend(self._collect_zebra_pairs(mount_id, zebra_signs))
        return {"REPORT_TYPE": "ADDED DOUBLE SIDED ZEBRA CROSSINGS", "results": results}

    # ==================== Sanity Check Reports ====================

    @staticmethod
    def _build_found_in_database_report(
        objects_dict: dict,
        db_id_map: dict,
        report_type: str,
        include_ssurl: bool = False,
    ) -> dict[str, Any]:
        """Build a found-in-database report for any object type.

        Args:
            objects_dict (dict): Mapping of source_id to CSV row data.
            db_id_map (dict): Mapping of source_id to database id.
            report_type (str): REPORT_TYPE label string for the result dict.
            include_ssurl (bool): Whether to include csv_ssurl in each result entry.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for source_id, obj_data in objects_dict.items():
            db_id = db_id_map.get(source_id)
            if not db_id:
                continue
            entry: dict[str, Any] = {
                "source_id": source_id,
                "db_id": str(db_id),
                "status": obj_data.get(CSVHeadersV2.status),
            }
            if include_ssurl:
                entry["csv_ssurl"] = obj_data.get(CSVHeadersV2.attachment_url, "")
            results.append(entry)
        return {"REPORT_TYPE": report_type, "results": results}

    def _get_mounts_found_in_database_report(self) -> dict[str, Any]:
        """Report mounts from CSV that exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._build_found_in_database_report(
            self.mounts_by_id, self.mount_source_id_to_db_id, "MOUNTS FOUND IN DATABASE"
        )

    def _get_traffic_signs_found_in_database_report(self) -> dict[str, Any]:
        """Report traffic signs from CSV that exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._build_found_in_database_report(
            self.signs_by_id, self.sign_source_id_to_db_id, "TRAFFIC SIGNS FOUND IN DATABASE"
        )

    def _get_additional_signs_found_in_database_report(self) -> dict[str, Any]:
        """Report additional signs from CSV that exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._build_found_in_database_report(
            self.additional_signs_by_id,
            self.additional_sign_source_id_to_db_id,
            "ADDITIONAL SIGNS FOUND IN DATABASE",
            include_ssurl=True,
        )

    def _get_main_signs_with_parent_report(self) -> dict[str, Any]:
        """Report main traffic signs that have a parent sign reference.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for source_id, sign_data in self.signs_by_id.items():
            parent_source_id = sign_data.get(CSVHeadersV2.parent_sign_id, "")
            if not parent_source_id:
                continue
            sign_code = sign_data.get(CSVHeadersV2.code)
            parent_is_additional = parent_source_id in self.additional_signs_by_id
            parent_is_main_sign = parent_source_id in self.signs_by_id
            if parent_is_additional:
                parent_data = self.additional_signs_by_id[parent_source_id]
                parent_type = "additional_sign"
            elif parent_is_main_sign:
                parent_data = self.signs_by_id[parent_source_id]
                parent_type = "main_sign"
            else:
                parent_data = None
                parent_type = "not_found_in_csv"
            parent_code = parent_data.get(CSVHeadersV2.code) if parent_data else None
            results.append(
                {
                    "sign_source_id": source_id,
                    "sign_device_code": sign_code,
                    "sign_status": sign_data.get(CSVHeadersV2.status),
                    "parent_source_id": parent_source_id,
                    "parent_device_code": parent_code,
                    "parent_type": parent_type,
                    "parent_status": parent_data.get(CSVHeadersV2.status) if parent_data else None,
                }
            )
        return {"REPORT_TYPE": "MAIN SIGNS WITH PARENT", "results": results}

    def _get_mounts_without_any_signs_report(self) -> dict[str, Any]:
        """Report mounts from CSV that have no signs, additional signs or signposts attached.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        mount_ids_with_signs: set[str] = set()
        for collections in (self.signs_by_mount_id, self.additional_signs_by_mount_id, self.signposts_by_mount_id):
            mount_ids_with_signs.update(collections.keys())
        results = [
            {
                "mount_source_id": mount_id,
                "status": mount_data.get(CSVHeadersV2.status),
            }
            for mount_id, mount_data in self.mounts_by_id.items()
            if mount_id not in mount_ids_with_signs
        ]
        return {"REPORT_TYPE": "MOUNTS WITHOUT ANY SIGNS", "results": results}

    def _get_mounts_with_removed_signs_report(self) -> dict[str, Any]:
        """Report mounts that have at least one removed sign.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        mounts_with_removed_signs: set[str] = set()
        for sign_data in self.signs_by_status["Removed"]:
            mount_source_id = sign_data.get(CSVHeadersV2.mount_id, "")
            if mount_source_id:
                mounts_with_removed_signs.add(mount_source_id)
        for sign_data in self.additional_signs_by_status["Removed"]:
            mount_source_id = sign_data.get(CSVHeadersV2.mount_id, "")
            if mount_source_id:
                mounts_with_removed_signs.add(mount_source_id)

        results = []
        for mount_source_id in mounts_with_removed_signs:
            mount_data = self.mounts_by_id.get(mount_source_id)
            if not mount_data:
                continue
            location = self._georeferenced_point_from_csv_row(mount_data)
            removed_signs_ssurls = [
                sign.get(CSVHeadersV2.attachment_url, "")
                for sign in self.signs_by_status["Removed"]
                if sign.get(CSVHeadersV2.mount_id, "") == mount_source_id
            ] + [
                sign.get(CSVHeadersV2.attachment_url, "")
                for sign in self.additional_signs_by_status["Removed"]
                if sign.get(CSVHeadersV2.mount_id, "") == mount_source_id
            ]
            results.append(
                {
                    "mount_source_id": mount_source_id,
                    "location": location.ewkt,
                    "removed_signs_ssurls": [url for url in removed_signs_ssurls if url],
                }
            )
        return {"REPORT_TYPE": "MOUNTS WITH REMOVED SIGNS", "results": results}

    # ==================== CSV-to-DB Location Distance Reports ====================

    @staticmethod
    def _build_csv_to_db_location_results(
        csv_objects: dict[str, dict],
        db_location_map: dict[str, tuple],
    ) -> list[dict[str, Any]]:
        """Build location distance result rows by comparing CSV coordinates to DB locations.

        Args:
            csv_objects (dict[str, dict]): Mapping of source_id to CSV row data.
            db_location_map (dict[str, tuple]): Mapping of source_id to (db_id, location) tuples.

        Returns:
            list[dict[str, Any]]: List of result dicts with source_id, db_id, status,
                csv_code, db_code, csv_mount_type, db_mount_type, csv/db coordinates, distance, link, and db_ssurl.
        """
        from .traffic_sign_data_v2_data_loading import DataLoadingMixin

        results = []
        for source_id, csv_row in csv_objects.items():
            db_entry = db_location_map.get(source_id)
            if not db_entry:
                continue
            db_id, db_location, *extra = db_entry
            db_ssurl = extra[0] if extra else None
            db_code = extra[1] if len(extra) > 1 else None
            db_mount_type = extra[2] if len(extra) > 2 else None
            csv_point = DataLoadingMixin._point_from_csv_row(csv_row)
            if csv_point is None or db_location is None:
                continue
            db_point = Point(db_location.x, db_location.y, 0.0)
            results.append(
                {
                    "source_id": source_id,
                    "db_id": str(db_id),
                    "status": csv_row.get(CSVHeadersV2.status),
                    "csv_code": csv_row.get(CSVHeadersV2.code),
                    "db_code": db_code,
                    "csv_mount_type": csv_row.get(CSVHeadersV2.mount_type),
                    "db_mount_type": db_mount_type,
                    "csv_x": csv_row.get(CSVHeadersV2.coord_x),
                    "csv_y": csv_row.get(CSVHeadersV2.coord_y),
                    "db_x": db_location.x,
                    "db_y": db_location.y,
                    "distance": csv_point.distance(db_point),
                    "link": csv_row.get(CSVHeadersV2.attachment_url),
                    "db_ssurl": db_ssurl,
                }
            )
        return results

    def _get_mount_csv_to_db_location_distance_report(self) -> dict[str, Any]:
        """Report distance between CSV location and database location for each mount.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._build_csv_to_db_location_results(self.mounts_by_id, self.mount_source_id_to_db_location)
        return {"REPORT_TYPE": "MOUNT CSV TO DB LOCATION DISTANCE", "results": results}

    def _get_traffic_sign_csv_to_db_location_distance_report(self) -> dict[str, Any]:
        """Report distance between CSV location and database location for each traffic sign.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._build_csv_to_db_location_results(self.signs_by_id, self.sign_source_id_to_db_location)
        return {"REPORT_TYPE": "TRAFFIC SIGN CSV TO DB LOCATION DISTANCE", "results": results}

    def _get_additional_sign_csv_to_db_location_distance_report(self) -> dict[str, Any]:
        """Report distance between CSV location and database location for each additional sign.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._build_csv_to_db_location_results(
            self.additional_signs_by_id, self.additional_sign_source_id_to_db_location
        )
        return {"REPORT_TYPE": "ADDITIONAL SIGN CSV TO DB LOCATION DISTANCE", "results": results}

    def _get_signpost_csv_to_db_location_distance_report(self) -> dict[str, Any]:
        """Report distance between CSV location and database location for each signpost.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._build_csv_to_db_location_results(self.signposts_by_id, self.signpost_source_id_to_db_location)
        return {"REPORT_TYPE": "SIGNPOST CSV TO DB LOCATION DISTANCE", "results": results}

    def _get_non_existing_mounts_for_signposts(self) -> dict[str, Any]:
        """Report signposts with non-existing mount references.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for sign_id, mount_id in self.no_mounts_per_signpost_id.items():
            sign_data = self.signposts_by_id.get(sign_id, {})
            mount_data = self.mounts_by_id.get(mount_id, {})
            results.append(
                {
                    "signpost_source_id": sign_id,
                    "mount_source_id": mount_id,
                    "devicetypecode": sign_data.get(CSVHeadersV2.code, ""),
                    "status": sign_data.get(CSVHeadersV2.status, ""),
                    "internal_status": sign_data.get("internal_status", ""),
                    "csv_ssurl": sign_data.get(CSVHeadersV2.attachment_url, ""),
                    "mount_ssurl": mount_data.get(CSVHeadersV2.attachment_url, ""),
                }
            )
        return {"REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNPOSTS", "results": results}

    def _get_signposts_that_are_both_parent_and_child_report(self) -> dict[str, Any]:
        """Report signposts that are marked as a parent of another signpost but are also a child of some other signpost.

        A signpost is considered a *parent* when at least one other signpost in the CSV references it via
        the ``parent_sign_id`` field (``lisäkilven_päämerkin_id``).  A signpost is considered a *child*
        when its own ``parent_sign_id`` field points to another signpost in the CSV.  This report flags
        all signposts that satisfy **both** conditions simultaneously, which indicates a data quality issue
        in the input data.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        signpost_ids: set[str] = self.signposts_by_id.keys()
        parent_ids: set[str] = {
            data.get(CSVHeadersV2.parent_sign_id, "")
            for data in self.signposts_by_id.values()
            if data.get(CSVHeadersV2.parent_sign_id, "") in signpost_ids
        }
        results = []
        for sign_id, data in self.signposts_by_id.items():
            own_parent_id = data.get(CSVHeadersV2.parent_sign_id, "")
            is_child = own_parent_id in signpost_ids
            is_parent = sign_id in parent_ids
            if is_child and is_parent:
                parent_data = self.signposts_by_id.get(own_parent_id, {})
                results.append(
                    {
                        "signpost_source_id": sign_id,
                        "devicetypecode": data.get(CSVHeadersV2.code, ""),
                        "status": data.get(CSVHeadersV2.status, ""),
                        "internal_status": data.get("internal_status", ""),
                        "parent_signpost_source_id": own_parent_id,
                        "parent_devicetypecode": parent_data.get(CSVHeadersV2.code, ""),
                        "parent_status": parent_data.get(CSVHeadersV2.status, ""),
                        "csv_ssurl": data.get(CSVHeadersV2.attachment_url, ""),
                        "parent_csv_ssurl": parent_data.get(CSVHeadersV2.attachment_url, ""),
                    }
                )
        return {"REPORT_TYPE": "SIGNPOSTS THAT ARE BOTH PARENT AND CHILD", "results": results}

    def _get_signposts_found_in_database_report(self) -> dict[str, Any]:
        """Report all signposts from CSV that exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._build_found_in_database_report(
            self.signposts_by_id,
            self.signpost_source_id_to_db_id,
            "SIGNPOSTS FOUND IN DATABASE",
            include_ssurl=True,
        )

    def _get_removed_parents_referenced_by_active_additional_signs(self) -> dict[str, Any]:
        """Report removed traffic signs or signposts used as parent by active additional signs.

        Finds all additional signs that are not marked as Removed but reference a parent
        (traffic sign or signpost) that is marked as Removed.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result entry contains additional_sign_source_id, additional_sign_code,
                additional_sign_status, parent_source_id, parent_code, parent_status, and parent_type.
        """
        results = []
        for source_id, add_sign in self.additional_signs_by_id.items():
            if add_sign.get(CSVHeadersV2.status) == "Removed":
                continue
            parent_source_id = add_sign.get(CSVHeadersV2.parent_sign_id)
            if not parent_source_id:
                continue
            parent_data, parent_type = self._resolve_parent_data_and_type(parent_source_id)
            if parent_data is None or parent_data.get(CSVHeadersV2.status) != "Removed":
                continue
            results.append(
                {
                    "additional_sign_source_id": source_id,
                    "additional_sign_code": add_sign.get(CSVHeadersV2.code),
                    "additional_sign_status": add_sign.get(CSVHeadersV2.status),
                    "parent_source_id": parent_source_id,
                    "parent_code": parent_data.get(CSVHeadersV2.code),
                    "parent_status": parent_data.get(CSVHeadersV2.status),
                    "parent_type": parent_type,
                    "additional_sign_ssurl": add_sign.get(CSVHeadersV2.attachment_url, ""),
                }
            )
        return {"REPORT_TYPE": "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT", "results": results}

    def _resolve_parent_data_and_type(self, parent_source_id: str) -> tuple[dict | None, str | None]:
        """Resolve parent CSV row data and type label for a given parent source ID.

        Checks traffic signs first, then signposts.

        Args:
            parent_source_id (str): The source ID of the parent sign or signpost.

        Returns:
            tuple[dict | None, str | None]: A tuple of (parent_data, parent_type).
                parent_type is 'traffic_sign', 'signpost', or None if not found.
        """
        if parent_source_id in self.signs_by_id:
            return self.signs_by_id[parent_source_id], "traffic_sign"
        if parent_source_id in self.signposts_by_id:
            return self.signposts_by_id[parent_source_id], "signpost"
        return None, None

    def _collect_invalid_location_objects(
        self, objects: list, object_type: str, id_key: str, include_device_code: bool
    ) -> list[dict[str, Any]]:
        """Collect Removed objects whose location fails the geometry legit check.

        Args:
            objects (list): List of CSV row dicts for a given object category and status.
            object_type (str): Human-readable type label.
            id_key (str): Result dict key to use for the source_id value.
            include_device_code (bool): Whether to include 'device_code' in each result entry.

        Returns:
            list[dict[str, Any]]: List of result dicts for objects with invalid locations.
        """
        results = []
        for obj in objects:
            location = self._georeferenced_point_from_csv_row(obj)
            if not geometry_is_legit(location):
                entry: dict[str, Any] = {"object_type": object_type, id_key: obj.get(CSVHeadersV2.id)}
                if include_device_code:
                    entry["device_code"] = obj.get(CSVHeadersV2.code)
                entry["location"] = location.ewkt
                results.append(entry)
        return results
