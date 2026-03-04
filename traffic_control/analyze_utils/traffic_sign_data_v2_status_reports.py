"""Status-based report methods mixin for TrafficSignAnalyzerV2."""
from datetime import datetime
from typing import Any

from .traffic_sign_data_v2_constants import CSVHeadersV2


class StatusReportsMixin:
    """Mixin providing status distribution, status record, and database-missing reports."""

    # ==================== Status-Based Reports ====================

    def _get_status_distribution_report(self):
        """Report count and percentage of objects by status."""

        def get_stats(objects_by_status, object_type):
            total = sum(len(objects) for objects in objects_by_status.values())
            stats = []
            for status, objects in objects_by_status.items():
                count = len(objects)
                percentage = (count / total * 100) if total > 0 else 0
                code_breakdown = {}
                if object_type in ["traffic_sign", "additional_sign"]:
                    for obj in objects:
                        code = obj.get(CSVHeadersV2.code, "unknown")
                        code_breakdown[code] = code_breakdown.get(code, 0) + 1
                stats.append(
                    {
                        "object_type": object_type,
                        "status": status,
                        "count": count,
                        "percentage": f"{percentage:.2f}%",
                        "code_breakdown": code_breakdown if code_breakdown else None,
                    }
                )
            return stats

        results = []
        results.extend(get_stats(self.mounts_by_status, "mount"))
        results.extend(get_stats(self.signs_by_status, "traffic_sign"))
        results.extend(get_stats(self.additional_signs_by_status, "additional_sign"))
        return {"REPORT_TYPE": "STATUS DISTRIBUTION", "results": results}

    def _get_invalid_status_report(self):
        """Report objects with invalid status values."""
        results = []
        for obj in self.mounts_by_status["invalid"]:
            results.append(
                {
                    "object_type": "mount",
                    "mount_source_id": obj.get(CSVHeadersV2.id),
                    "invalid_status": obj.get(CSVHeadersV2.status, ""),
                }
            )
        for obj in self.signs_by_status["invalid"]:
            results.append(
                {
                    "object_type": "traffic_sign",
                    "sign_source_id": obj.get(CSVHeadersV2.id),
                    "invalid_status": obj.get(CSVHeadersV2.status, ""),
                }
            )
        for obj in self.additional_signs_by_status["invalid"]:
            results.append(
                {
                    "object_type": "additional_sign",
                    "additional_sign_source_id": obj.get(CSVHeadersV2.id),
                    "invalid_status": obj.get(CSVHeadersV2.status, ""),
                }
            )
        return {"REPORT_TYPE": "INVALID STATUS VALUES", "results": results}

    def _get_status_records_report(self, status: str) -> dict[str, Any]:
        """Report all records with specified status.

        Args:
            status (str): Status to filter by (e.g., "Changed", "Unchanged").

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        results.extend(
            self._get_sign_status_records(
                self.signs_by_status.get(status, []),
                self.sign_reals_by_source_id,
                self.sign_reals_legacy_codes_by_source_id,
                "traffic_sign",
            )
        )
        results.extend(
            self._get_sign_status_records(
                self.additional_signs_by_status.get(status, []),
                self.additional_sign_reals_by_source_id,
                self.additional_sign_reals_legacy_codes_by_source_id,
                "additional_sign",
            )
        )
        return {"REPORT_TYPE": f"{status.upper()} RECORDS", "results": results}

    @staticmethod
    def _get_sign_status_records(
        sign_objects: list,
        db_codes_mapping: dict[str, str | None],
        legacy_codes_mapping: dict[str, str | None],
        object_type: str,
    ) -> list[dict[str, Any]]:
        """Generate status records for signs (traffic or additional).

        Args:
            sign_objects (list): List of sign objects from CSV.
            db_codes_mapping (dict[str, str | None]): Mapping of source_id to device_type code from database.
            legacy_codes_mapping (dict[str, str | None]): Mapping of source_id to legacy_code from database.
            object_type (str): Type of object ("traffic_sign" or "additional_sign").

        Returns:
            list[dict[str, Any]]: List of sign record dictionaries.
        """
        results = []
        for obj in sign_objects:
            source_id = obj.get(CSVHeadersV2.id)
            old_device_code = db_codes_mapping.get(source_id)
            new_device_code = obj.get(CSVHeadersV2.code)
            old_legacy_code = legacy_codes_mapping.get(source_id)
            new_legacy_code = obj.get(CSVHeadersV2.code)
            results.append(
                {
                    "object_type": object_type,
                    "source_id": source_id,
                    "old_device_code": old_device_code,
                    "old_legacy_code": old_legacy_code,
                    "new_device_code": new_device_code,
                    "new_legacy_code": new_legacy_code,
                    "has_changed": old_device_code != new_device_code,
                }
            )
        return results

    def _get_change_records_report(self) -> dict[str, Any]:
        """Report all records with status=Changed.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_status_records_report("Changed")

    def _get_unchanged_records_report(self) -> dict[str, Any]:
        """Report all records with status=Unchanged.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_status_records_report("Unchanged")

    def _get_new_records_report(self) -> dict[str, Any]:
        """Report all records with status=New.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_status_records_report("New")

    def _get_remove_records_report(self) -> dict[str, Any]:
        """Report all records with status=Removed.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each entry includes object_type, the id field, an optional device_code,
                and found_in_database indicating whether the object exists in the database.
        """
        results = []
        categories = [
            (self.mounts_by_status["Removed"], "mount", "mount_source_id", False, self.mount_reals_by_source_id_set),
            (self.signs_by_status["Removed"], "traffic_sign", "sign_source_id", True, self.sign_reals_by_source_id),
            (
                self.additional_signs_by_status["Removed"],
                "additional_sign",
                "additional_sign_source_id",
                True,
                self.additional_sign_reals_by_source_id,
            ),
            (
                self.signposts_by_status["Removed"],
                "signpost",
                "signpost_source_id",
                True,
                self.signpost_reals_by_source_id,
            ),
        ]
        for objects, object_type, id_key, include_device_code, db_source_ids in categories:
            for obj in objects:
                source_id = obj.get(CSVHeadersV2.id)
                entry: dict[str, Any] = {
                    "object_type": object_type,
                    id_key: source_id,
                    "found_in_database": source_id in db_source_ids,
                }
                if include_device_code:
                    entry["device_code"] = obj.get(CSVHeadersV2.code)
                results.append(entry)
        return {"REPORT_TYPE": "REMOVE RECORDS", "results": results}

    def _get_remove_with_invalid_location_report(self):
        """Report Removed status records with invalid locations."""
        results = []
        categories = [
            (self.mounts_by_status["Removed"], "mount", "mount_source_id", False),
            (self.signs_by_status["Removed"], "traffic_sign", "sign_source_id", True),
            (self.additional_signs_by_status["Removed"], "additional_sign", "additional_sign_source_id", True),
            (self.signposts_by_status["Removed"], "signpost", "signpost_source_id", True),
        ]
        for objects, object_type, id_key, include_device_code in categories:
            results += self._collect_invalid_location_objects(objects, object_type, id_key, include_device_code)
        return {"REPORT_TYPE": "REMOVE WITH INVALID LOCATION", "results": results}

    @staticmethod
    def _get_sign_scanned_at(date_str):
        """Parse scanned_at timestamp string."""
        return datetime.strptime(date_str + "00", "%Y/%m/%d %H:%M:%S%z")

    _OBJECT_TYPE_ID_KEY = {
        "mount": "mount_source_id",
        "traffic_sign": "sign_source_id",
        "additional_sign": "additional_sign_source_id",
        "signpost": "signpost_source_id",
    }

    @staticmethod
    def _validate_timestamp(obj: dict, object_type: str) -> dict | None:
        """Validate a single object's timestamp field.

        Args:
            obj (dict): CSV row dictionary.
            object_type (str): One of 'mount', 'traffic_sign', 'additional_sign', 'signpost'.

        Returns:
            dict | None: Error dict if timestamp is invalid, None otherwise.
        """
        timestamp_str = obj.get(CSVHeadersV2.scanned_at, "")
        if not timestamp_str:
            return None
        try:
            StatusReportsMixin._get_sign_scanned_at(timestamp_str)
        except (ValueError, AttributeError):
            id_field = StatusReportsMixin._OBJECT_TYPE_ID_KEY.get(object_type, "source_id")
            return {
                "object_type": object_type,
                id_field: obj.get(CSVHeadersV2.id),
                "invalid_timestamp": timestamp_str,
            }
        return None

    def _get_timestamp_format_validation_report(self):
        """Report records with invalid timestamp formats."""
        results = []
        categories = [
            (self.mounts_by_id.values(), "mount"),
            (self.signs_by_id.values(), "traffic_sign"),
            (self.additional_signs_by_id.values(), "additional_sign"),
            (self.signposts_by_id.values(), "signpost"),
        ]
        for objects, object_type in categories:
            for obj in objects:
                if error := self._validate_timestamp(obj, object_type):
                    results.append(error)
        return {"REPORT_TYPE": "TIMESTAMP FORMAT ERRORS", "results": results}

    def _get_invalid_device_type_codes_report(self) -> dict[str, Any]:
        """Report device type codes found in CSV that don't exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        seen_codes: set[str] = set()
        for source_id, sign_data in self.signs_by_id.items():
            code = sign_data.get(CSVHeadersV2.code, "")
            if code and code not in self.code_to_device_type_id:
                seen_codes.add(code)
                results.append(
                    {
                        "object_type": "traffic_sign",
                        "sign_source_id": source_id,
                        "invalid_code": code,
                        "status": sign_data.get(CSVHeadersV2.status),
                        "csv_row": self._row_to_csv_line(sign_data, self.delimiter),
                    }
                )
        for source_id, sign_data in self.additional_signs_by_id.items():
            code = sign_data.get(CSVHeadersV2.code, "")
            if code and code not in self.code_to_device_type_id:
                seen_codes.add(code)
                results.append(
                    {
                        "object_type": "additional_sign",
                        "additional_sign_source_id": source_id,
                        "invalid_code": code,
                        "status": sign_data.get(CSVHeadersV2.status),
                        "csv_row": self._row_to_csv_line(sign_data, self.delimiter),
                    }
                )
        return {"REPORT_TYPE": "INVALID DEVICE TYPE CODES", "results": results}

    def _get_status_internal_status_mismatch_report(self) -> dict[str, Any]:
        """Report mismatches between CSV status and calculated internal_status.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        expected_mapping = {
            "New": {"new"},
            "Unchanged": {"unchanged"},
            "Changed": {"changed"},
            "Removed": {"unchanged", "changed"},
        }
        results = []
        results += self._collect_status_mismatch_records(
            self.signs_by_id,
            self.sign_reals_by_source_id,
            self.sign_reals_legacy_codes_by_source_id,
            "traffic_sign",
            expected_mapping,
        )
        results += self._collect_status_mismatch_records(
            self.additional_signs_by_id,
            self.additional_sign_reals_by_source_id,
            self.additional_sign_reals_legacy_codes_by_source_id,
            "additional_sign",
            expected_mapping,
        )
        results += self._collect_status_mismatch_records(
            self.signposts_by_id,
            self.signpost_reals_by_source_id,
            self.signpost_reals_legacy_codes_by_source_id,
            "signpost",
            expected_mapping,
        )
        return {"REPORT_TYPE": "STATUS AND INTERNAL_STATUS MISMATCH", "results": results}

    _MISMATCH_REASONS: dict[tuple[str, str], str] = {
        ("New", "unchanged"): "Marked as New but already exists in database",
        ("New", "changed"): "Marked as New but already exists in database",
        ("Unchanged", "new"): "Marked as Unchanged but not found in database",
        ("Unchanged", "changed"): "Marked as Unchanged but device type code differs from database",
        ("Changed", "new"): "Marked as Changed but not found in database",
        ("Changed", "unchanged"): "Marked as Changed but device type code matches database",
        ("Removed", "new"): "Marked as Removed but not found in database",
    }

    @staticmethod
    def _resolve_mismatch_reason(status: str, status_normalized: str, internal_status: str) -> str:
        """Resolve the human-readable mismatch reason for a status/internal_status pair.

        Args:
            status (str): Raw CSV status value.
            status_normalized (str): Capitalised CSV status value.
            internal_status (str): Computed internal status value.

        Returns:
            str: Description of why the statuses are considered mismatched.
        """
        key = (status_normalized, internal_status)
        return StatusReportsMixin._MISMATCH_REASONS.get(
            key,
            f"Status '{status}' incompatible with internal_status '{internal_status}'",
        )

    @staticmethod
    def _collect_status_mismatch_records(
        signs_dict: dict,
        db_codes_map: dict,
        db_legacy_codes_map: dict,
        object_type: str,
        expected_mapping: dict,
    ) -> list[dict[str, Any]]:
        """Collect status/internal_status mismatch records for a set of signs.

        Args:
            signs_dict (dict): Mapping of source_id to sign data dicts.
            db_codes_map (dict): Mapping of source_id to DB device_type code.
            db_legacy_codes_map (dict): Mapping of source_id to DB device_type legacy_code.
            object_type (str): Human-readable type label.
            expected_mapping (dict): Mapping of CSV status to expected set of internal_status values.

        Returns:
            list[dict[str, Any]]: List of mismatch result dicts.
        """
        records = []
        for source_id, sign_data in signs_dict.items():
            status = sign_data.get(CSVHeadersV2.status, "")
            internal_status = sign_data.get("internal_status", "")
            status_normalized = status.capitalize() if status else ""
            if status_normalized not in expected_mapping:
                continue
            if internal_status in expected_mapping[status_normalized]:
                continue
            reason = StatusReportsMixin._resolve_mismatch_reason(status, status_normalized, internal_status)
            records.append(
                {
                    "object_type": object_type,
                    "source_id": source_id,
                    "status": status,
                    "internal_status": internal_status,
                    "db_code": db_codes_map.get(source_id),
                    "db_legacy_code": db_legacy_codes_map.get(source_id),
                    "csv_code": sign_data.get(CSVHeadersV2.code, ""),
                    "csv_ssurl": sign_data.get(CSVHeadersV2.attachment_url, ""),
                    "mismatch_reason": reason,
                }
            )
        return records

    def _get_missing_mounts_from_database_report(self) -> dict[str, Any]:
        """Report mounts with non-New status that don't exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        for status in ["Unchanged", "Changed", "Removed"]:
            for obj in self.mounts_by_status[status]:
                source_id = obj.get(CSVHeadersV2.id)
                if source_id in self.mount_reals_by_source_id_set:
                    continue
                traffic_sign_codes = [
                    sign.get(CSVHeadersV2.code, "") for sign in obj.get("signs", []) if sign.get(CSVHeadersV2.code, "")
                ]
                additional_sign_codes = [
                    sign.get(CSVHeadersV2.code, "")
                    for sign in obj.get("additional_signs", [])
                    if sign.get(CSVHeadersV2.code, "")
                ]
                results.append(
                    {
                        "mount_source_id": source_id,
                        "status": status,
                        "mount_type": obj.get(CSVHeadersV2.mount_type),
                        "traffic_sign_codes": ", ".join(traffic_sign_codes) if traffic_sign_codes else "",
                        "additional_sign_codes": ", ".join(additional_sign_codes) if additional_sign_codes else "",
                        "is_orphan": not traffic_sign_codes and not additional_sign_codes,
                        "found_in_previous_csv": source_id in self.old_mount_source_ids,
                    }
                )
        return {"REPORT_TYPE": "MISSING MOUNTS FROM DATABASE", "results": results}

    @staticmethod
    def _collect_missing_from_database(
        signs_by_status: dict,
        db_source_id_set: set,
        id_key: str,
        old_source_ids: set,
        include_ssurl: bool = False,
    ) -> list[dict[str, Any]]:
        """Collect sign records with non-New status that are absent from the database.

        Args:
            signs_by_status (dict): Mapping of status string to list of CSV row dicts.
            db_source_id_set (set): Set of source_ids known to exist in the database.
            id_key (str): Result dict key to use for the source_id value.
            old_source_ids (set): Set of source_ids found in the previous CSV file.
            include_ssurl (bool): Whether to include csv_ssurl in each result entry.

        Returns:
            list[dict[str, Any]]: List of result dicts for missing objects.
        """
        results = []
        for status in ["Unchanged", "Changed", "Removed"]:
            for obj in signs_by_status[status]:
                source_id = obj.get(CSVHeadersV2.id)
                if source_id in db_source_id_set:
                    continue
                entry: dict[str, Any] = {
                    id_key: source_id,
                    "status": status,
                    "device_code": obj.get(CSVHeadersV2.code),
                    "found_in_previous_csv": source_id in old_source_ids,
                }
                if include_ssurl:
                    entry["csv_ssurl"] = obj.get(CSVHeadersV2.attachment_url, "")
                results.append(entry)
        return results

    def _get_missing_traffic_signs_from_database_report(self) -> dict[str, Any]:
        """Report traffic signs with non-New status that don't exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._collect_missing_from_database(
            self.signs_by_status,
            set(self.sign_reals_by_source_id),
            "sign_source_id",
            self.old_sign_source_ids,
            include_ssurl=True,
        )
        return {"REPORT_TYPE": "MISSING TRAFFIC SIGNS FROM DATABASE", "results": results}

    def _get_missing_additional_signs_from_database_report(self) -> dict[str, Any]:
        """Report additional signs with non-New status that don't exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._collect_missing_from_database(
            self.additional_signs_by_status,
            set(self.additional_sign_reals_by_source_id),
            "additional_sign_source_id",
            self.old_sign_source_ids,
        )
        return {"REPORT_TYPE": "MISSING ADDITIONAL SIGNS FROM DATABASE", "results": results}

    def _get_missing_signposts_from_database_report(self) -> dict[str, Any]:
        """Report signposts with non-New status that don't exist in the database.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = self._collect_missing_from_database(
            self.signposts_by_status,
            set(self.signpost_reals_by_source_id),
            "signpost_source_id",
            self.old_sign_source_ids,
            include_ssurl=True,
        )
        return {"REPORT_TYPE": "MISSING SIGNPOSTS FROM DATABASE", "results": results}
