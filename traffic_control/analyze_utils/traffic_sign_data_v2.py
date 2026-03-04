import csv
from datetime import datetime
from typing import Any

from django.conf import settings
from django.contrib.gis.geos import Point

from traffic_control.geometry_utils import geometry_is_legit
from traffic_control.models.additional_sign import AdditionalSignReal
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.models.mount import MountReal
from traffic_control.models.traffic_sign import TrafficSignReal

from .traffic_sign_data import  TrafficSignImporter

# Constants for V2 analyzer
VALID_STATUS_VALUES = ["new", "unchanged", "changed", "removed"]  # Lowercase for case-insensitive comparison
ZEBRA_CROSSING_LEFT_CODES = ["511", "5112", "E1_2"]
ZEBRA_CROSSING_RIGHT_CODES = ["5111", "E1"]
ZEBRA_CROSSING_ALL_CODES = ZEBRA_CROSSING_LEFT_CODES + ZEBRA_CROSSING_RIGHT_CODES
DIRECTION_TOLERANCE = 20  # degrees tolerance for 180° difference


class CSVHeadersV2:
    """CSV headers for new traffic sign data format with status field"""

    id = "id"
    attachment_url = "ssurl"
    code = "merkkikoodi"
    color = "taustaväri"
    condition = "merkin_ehto"
    coord_x = "x"
    coord_y = "y"
    coord_z = "z"
    direction = "atsimuutti"
    height = "korkeus"
    mount_id = "kiinnityskohta_id"
    mount_type = "tyyppi"
    number_code = "numerokoodi"
    parent_sign_id = "lisäkilven_päämerkin_id"
    scanned_at = "tallennusajankohta"
    sign_mount_type = "kiinnitys"
    status = "status"  # New field
    txt = "teksti"
    location_specifier = "sijaintitarkenne"


class TrafficSignAnalyzerV2:
    """Analyzer for new traffic sign CSV format with status field.

    This analyzer processes CSV files containing traffic sign data in V2 format
    with status tracking (New/unchanged/Change/Remove) and generates comprehensive
    analysis reports including status distribution, duplicate detection, and
    double-sided zebra crossing identification.
    """

    def __init__(
        self,
        mount_file: str,
        sign_file: str,
        previous_mount_file: str | None = None,
        previous_sign_file: str | None = None,
        delimiter: str = ","
    ) -> None:
        """Initialize TrafficSignAnalyzerV2 with CSV files.

        Args:
            mount_file (str): Path to the mount CSV file.
            sign_file (str): Path to the sign CSV file (contains both traffic signs and additional signs).
            previous_mount_file (str | None): Path to the previous mount CSV file for tracking source_ids. Defaults to None.
            previous_sign_file (str | None): Path to the previous sign CSV file for tracking source_ids. Defaults to None.
            delimiter (str): CSV delimiter character. Defaults to ",".
        """
        self.delimiter = delimiter

        # Read CSV files into memory once at initialization
        self.mount_rows = self._read_csv_file(mount_file)
        self.sign_rows = self._read_csv_file(sign_file)

        # Read previous CSV files if provided
        self.previous_mount_rows = self._read_csv_file(previous_mount_file) if previous_mount_file else []
        self.previous_sign_rows = self._read_csv_file(previous_sign_file) if previous_sign_file else []

        # Build sets of source IDs from previous import for comparison
        self.old_mount_source_ids = self._build_source_id_set(self.previous_mount_rows)
        self.old_sign_source_ids = self._build_source_id_set(self.previous_sign_rows)

        # Initialize tracking for filtering and enrichment
        self.filtered_signs = []  # Rows removed due to invalid codes
        self.enriched_signs = []  # Rows that had location_specifier added

        # Filter and enrich sign rows
        self.sign_rows = self._filter_and_enrich_sign_rows(self.sign_rows)

        # Query device types once at initialization for performance
        self.code_to_device_type_id = self._build_code_to_device_type_mapping()
        # Load CSV data
        self.mounts_by_id = self._get_objects_by_id(self.mount_rows, CSVHeadersV2.id, None, flat=True)
        self.all_signs_by_id = self._get_objects_by_id(self.sign_rows, CSVHeadersV2.id, None, flat=True)
        self.signs_by_id = self._get_signs_by_id(self.sign_rows, CSVHeadersV2.id, flat=True)
        self.signs_by_mount_id = self._get_signs_by_mount_id()
        self.additional_signs_by_id = self._get_additional_signs_by_id(self.sign_rows, CSVHeadersV2.id, flat=True)
        self.additional_signs_by_mount_id = self._get_additional_signs_by_mount_id()

        # Combine mounts with signs (reuse existing logic)
        self._combine_mounts_with_signs(self.mounts_by_id, self.additional_signs_by_mount_id, self.signs_by_mount_id)

        # Calculate non-existing mounts
        self.no_mounts_per_sign_id = self._get_non_existing_mounts_by_sign_id()
        self.no_mounts_per_additional_sign_id = self._get_non_existing_mounts_by_additional_sign_id()

        # Segregate objects by status
        self.mounts_by_status = self._segregate_by_status(self.mounts_by_id.values())
        self.signs_by_status = self._segregate_by_status(self.signs_by_id.values())
        self.additional_signs_by_status = self._segregate_by_status(self.additional_signs_by_id.values())

        # Build DB source_id -> device_type.code maps for change record comparison
        self.mount_reals_by_source_id_set = self._build_mount_reals_by_source_id()
        self.sign_reals_by_source_id = self._build_sign_reals_by_source_id()
        self.additional_sign_reals_by_source_id = self._build_additional_sign_reals_by_source_id()

        # Build DB source_id -> db_id maps for sanity check reports
        self.mount_source_id_to_db_id = self._build_mount_source_id_to_db_id()
        self.sign_source_id_to_db_id = self._build_sign_source_id_to_db_id()
        self.additional_sign_source_id_to_db_id = self._build_additional_sign_source_id_to_db_id()

    def analyze(self) -> list[dict]:
        """Generate all analysis reports.

        Returns:
            list[dict]: List of report dictionaries, each containing 'REPORT_TYPE' and 'results' keys.
        """
        reports = [
            # Existing analysis reports
            self._get_non_existing_mounts_for_additional_signs(),
            self._get_non_existing_mounts_for_signs(),
            self._get_mount_distances(),
            self._get_additional_sign_distances(),
            self._get_sign_distances(),
            self._get_mountless_additional_signs(),
            self._get_signless_additional_signs(),
            self._get_mountless_signs(),
            # CSV preprocessing reports
            self._get_filtered_signs_report(),
            self._get_enriched_signs_report(),
            # New status-based reports
            self._get_status_distribution_report(),
            self._get_invalid_status_report(),
            self._get_change_records_report(),
            self._get_unchanged_records_report(),
            self._get_remove_records_report(),
            self._get_remove_with_invalid_location_report(),
            self._get_timestamp_format_validation_report(),
            self._get_invalid_device_type_codes_report(),
            self._get_missing_mounts_from_database_report(),
            self._get_missing_traffic_signs_from_database_report(),
            self._get_missing_additional_signs_from_database_report(),
            # New duplicate detection reports
            self._get_duplicate_signs_on_same_mount_by_device_type(),
            self._get_duplicate_signs_on_same_mount_exact_code(),
            self._get_added_double_sided_zebra_crossings(),
            # New sanity check reports
            self._get_mounts_found_in_database_report(),
            self._get_traffic_signs_found_in_database_report(),
            self._get_additional_signs_found_in_database_report(),
            self._get_main_signs_with_parent_report(),
            self._get_mounts_with_removed_signs_report(),
        ]
        return reports

    def _read_csv_file(self, csv_file_path: str) -> list[dict]:
        """Read CSV file into memory.

        Args:
            csv_file_path (str): Path to the CSV file.

        Returns:
            list[dict]: List of dictionaries representing CSV rows.
        """
        rows = []
        with open(csv_file_path) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            for row in reader:
                rows.append(row)
        return rows

    @staticmethod
    def _build_source_id_set(csv_rows: list[dict]) -> set[str]:
        """Build set of source IDs from CSV rows.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.

        Returns:
            set[str]: Set of source ID strings from the rows.
        """
        return {row.get(CSVHeadersV2.id, "").strip() for row in csv_rows if row.get(CSVHeadersV2.id, "").strip()}

    def _filter_and_enrich_sign_rows(self, sign_rows: list[dict]) -> list[dict]:
        """Filter out invalid sign codes and add location_specifier values.

        Removes rows where code is "x" or "not classified" (case insensitive).
        Adds location_specifier value of "4" for specific traffic sign codes.
        Tracks removed and enriched rows for reporting.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries.

        Returns:
            list[dict]: Filtered and enriched list of sign row dictionaries.
        """
        # Codes that should be filtered out (case insensitive)
        invalid_codes = {"x", "not classified"}

        # Codes that should have location_specifier = 4
        location_specifier_4_codes = [
            "4171", "4172", "418",
            "D3.1", "D3.1_2",
            "D3.2", "D3.2_2",
            "D3.3", "D3.3_2"
        ]

        filtered_rows = []
        for row in sign_rows:
            code = row.get(CSVHeadersV2.code, "").strip()

            # Filter out invalid codes (case insensitive)
            if code.lower() in invalid_codes:
                # Track removed row
                self.filtered_signs.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "code": code,
                    "reason": "invalid_code",
                })
                continue

            # Add location_specifier if not present and code matches
            location_specifier_value = row.get(CSVHeadersV2.location_specifier, "").strip()
            if not location_specifier_value and code in location_specifier_4_codes:
                # Track enrichment
                self.enriched_signs.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "code": code,
                    "field": "location_specifier",
                    "old_value": location_specifier_value if location_specifier_value else None,
                    "new_value": "4",
                })
                # Modify the row
                row[CSVHeadersV2.location_specifier] = "4"

            filtered_rows.append(row)

        return filtered_rows

    @staticmethod
    def _build_code_to_device_type_mapping() -> dict[str, Any]:
        """Build mapping from both code and legacy_code to device type ID.

        Returns:
            dict[str, Any]: Dictionary mapping device codes (both current and legacy) to device type IDs.
        """
        code_to_id = {}
        for dt in TrafficControlDeviceType.objects.all():
            code_to_id[dt.code] = dt.id
            if dt.legacy_code:
                code_to_id[dt.legacy_code] = dt.id
        return code_to_id

    @staticmethod
    def _build_mount_reals_by_source_id() -> set[str]:
        """Build set of source_ids for active MountReal objects in the database.

        Returns:
            set[str]: Set of source_ids for active mounts.
        """
        return {
            obj.source_id
            for obj in MountReal.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).only("source_id")
        }

    @staticmethod
    def _build_sign_reals_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.code for active TrafficSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type code.
        """
        return {
            obj.source_id: obj.device_type.code
            for obj in TrafficSignReal.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).select_related("device_type")
        }

    @staticmethod
    def _build_additional_sign_reals_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.code for active AdditionalSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type code.
        """
        return {
            obj.source_id: obj.device_type.code
            for obj in AdditionalSignReal.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).select_related("device_type")
        }

    @staticmethod
    def _build_mount_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for active MountReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return {
            obj.source_id: obj.id
            for obj in MountReal.objects.filter(source_name__startswith=TrafficSignImporter.SOURCE_NAME)
        }

    @staticmethod
    def _build_sign_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for active TrafficSignReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return {
            obj.source_id: obj.id
            for obj in TrafficSignReal.objects.filter(source_name__startswith=TrafficSignImporter.SOURCE_NAME)
        }

    @staticmethod
    def _build_additional_sign_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for active AdditionalSignReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return {
            obj.source_id: obj.id
            for obj in AdditionalSignReal.objects.filter(source_name__startswith=TrafficSignImporter.SOURCE_NAME)
        }

    def _get_objects_by_id(
        self, csv_rows: list[dict], id_field_name: str = CSVHeadersV2.id, filter_f=None, flat: bool = False
    ) -> dict:
        """Load objects from CSV rows with optional filtering.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.
            id_field_name (str): Name of the ID field in CSV. Defaults to CSVHeadersV2.id.
            filter_f: Optional filter function to apply to rows.
            flat (bool): If True, store single object per ID; if False, store list. Defaults to False.

        Returns:
            dict: Dictionary of objects indexed by ID.
        """
        objects_by_id = {}

        for row in csv_rows:
            if filter_f is None or filter_f(row):
                if not flat:
                    objects_by_id.setdefault(row[id_field_name], []).append(row)
                else:
                    objects_by_id[row[id_field_name]] = row

        return objects_by_id

    def _get_signs_by_id(self, csv_rows: list[dict], id_field_name: str = CSVHeadersV2.id, flat: bool = False) -> dict:
        """Get traffic signs (not additional signs) with distance calculations.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.
            id_field_name (str): Name of the ID field in CSV. Defaults to CSVHeadersV2.id.
            flat (bool): If True, store single object per ID; if False, store list. Defaults to False.

        Returns:
            dict: Dictionary of traffic signs indexed by ID with calculated distances to mounts.
        """
        signs = self._get_objects_by_id(
            csv_rows, id_field_name=id_field_name, filter_f=lambda x: not self._is_additional_sign(x), flat=flat
        )
        for k, data in signs.items():
            mount_data = self.mounts_by_id.get(data.get(CSVHeadersV2.mount_id), None)
            if mount_data:
                mount_point = Point(
                    float(mount_data[CSVHeadersV2.coord_x]), float(mount_data[CSVHeadersV2.coord_y]), 0.0
                )
                data["distance_to_mount"] = mount_point.distance(
                    Point(float(data[CSVHeadersV2.coord_x]), float(data[CSVHeadersV2.coord_y]), 0.0)
                )
            else:
                data["distance_to_mount"] = None
        return signs

    def _get_signs_by_mount_id(self) -> dict:
        """Group signs by mount ID.

        Returns:
            dict: Dictionary mapping mount IDs to lists of signs.
        """
        signs = {}
        for k, v in self.signs_by_id.items():
            signs.setdefault(v[CSVHeadersV2.mount_id], []).append(v)
        return signs

    def _get_additional_signs_by_id(
        self, csv_rows: list[dict], id_field_name: str = CSVHeadersV2.id, flat: bool = False
    ) -> dict:
        """Get additional signs with distance calculations.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.
            id_field_name (str): Name of the ID field in CSV. Defaults to CSVHeadersV2.id.
            flat (bool): If True, store single object per ID; if False, store list. Defaults to False.

        Returns:
            dict: Dictionary of additional signs indexed by ID with calculated distances.
        """
        additional_signs = self._get_objects_by_id(
            csv_rows, id_field_name=id_field_name, filter_f=self._is_additional_sign, flat=flat
        )
        for k, data in additional_signs.items():
            # Distance to mount
            mount_data = self.mounts_by_id.get(data.get(CSVHeadersV2.mount_id), None)
            if mount_data:
                mount_point = Point(
                    float(mount_data[CSVHeadersV2.coord_x]), float(mount_data[CSVHeadersV2.coord_y]), 0.0
                )
                data["distance_to_mount"] = mount_point.distance(
                    Point(float(data[CSVHeadersV2.coord_x]), float(data[CSVHeadersV2.coord_y]), 0.0)
                )
            else:
                data["distance_to_mount"] = None

            # Distance to parent sign
            parent_data = self.signs_by_id.get(data.get(CSVHeadersV2.parent_sign_id), None)
            if parent_data:
                parent_point = Point(
                    float(parent_data[CSVHeadersV2.coord_x]), float(parent_data[CSVHeadersV2.coord_y]), 0.0
                )
                data["distance_to_parent"] = parent_point.distance(
                    Point(float(data[CSVHeadersV2.coord_x]), float(data[CSVHeadersV2.coord_y]), 0.0)
                )
                data["parent_is_additional_sign"] = "No"
                data["parent_code"] = parent_data.get(CSVHeadersV2.code)
            else:
                parent_data = self.all_signs_by_id.get(data.get(CSVHeadersV2.parent_sign_id), None)
                if parent_data:
                    parent_point = Point(
                        float(parent_data[CSVHeadersV2.coord_x]), float(parent_data[CSVHeadersV2.coord_y]), 0.0
                    )
                    data["distance_to_parent"] = parent_point.distance(
                        Point(float(data[CSVHeadersV2.coord_x]), float(data[CSVHeadersV2.coord_y]), 0.0)
                    )
                    data["parent_is_additional_sign"] = "Yes"
                    data["parent_code"] = parent_data.get(CSVHeadersV2.code)
                else:
                    data["distance_to_parent"] = None
                    data["parent_is_additional_sign"] = None
                    data["parent_code"] = None
        return additional_signs

    def _get_additional_signs_by_mount_id(self):
        """Group additional signs by mount ID"""
        additional_signs = {}
        for k, v in self.additional_signs_by_id.items():
            additional_signs.setdefault(v[CSVHeadersV2.mount_id], []).append(v)
        return additional_signs

    @staticmethod
    def _combine_mounts_with_signs(mounts_by_id, additional_signs_by_mount_id, signs_by_mount_id):
        """Combine mounts with their attached signs"""
        for mount_id, data_d in mounts_by_id.items():
            data_d["additional_signs"] = []
            data_d["signs"] = []

            for entry in additional_signs_by_mount_id.get(mount_id, []):
                data_d["additional_signs"].append(entry)
            for entry in signs_by_mount_id.get(mount_id, []):
                data_d["signs"].append(entry)

    def _get_non_existing_mounts_by_sign_id(self):
        """Find signs with non-existing mount references"""
        return {
            x.get(CSVHeadersV2.id): x.get(CSVHeadersV2.mount_id)
            for x in filter(
                lambda x: x.get(CSVHeadersV2.mount_id).strip() not in self.mounts_by_id.keys(),
                self.signs_by_id.values(),
            )
        }

    def _get_non_existing_mounts_by_additional_sign_id(self):
        """Find additional signs with non-existing mount references"""
        return {
            x.get(CSVHeadersV2.id): x.get(CSVHeadersV2.mount_id)
            for x in filter(
                lambda x: x.get(CSVHeadersV2.mount_id).strip() not in self.mounts_by_id.keys(),
                self.additional_signs_by_id.values(),
            )
        }

    @staticmethod
    def _is_additional_sign(row):
        """Check if row represents an additional sign"""
        code = row[CSVHeadersV2.code]
        return code and code[0] in ["H", "8"]

    @staticmethod
    def _segregate_by_status(objects) -> dict[str, list]:
        """Segregate objects by status field.

        Args:
            objects: Iterable of objects with status field.

        Returns:
            dict[str, list]: Dictionary with status values as keys and lists of objects as values.
                Keys: 'New', 'Unchanged', 'Changed', 'Removed', 'invalid'.
        """
        by_status = {
            "New": [],
            "Unchanged": [],
            "Changed": [],
            "Removed": [],
            "invalid": [],
        }
        for obj in objects:
            status = obj.get(CSVHeadersV2.status, "").strip().lower()
            if status in VALID_STATUS_VALUES:
                # Capitalize first letter for consistent key naming
                status_key = status.capitalize()
                by_status[status_key].append(obj)
            else:
                by_status["invalid"].append(obj)
        return by_status

    # ==================== Existing Analysis Reports ====================

    def _get_non_existing_mounts_for_signs(self):
        """Report signs with non-existing mount references"""
        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS",
            "results": list(
                map(lambda x: {"sign_source_id": x[0], "mount_source_id": x[1]}, self.no_mounts_per_sign_id.items())
            ),
        }

    def _get_non_existing_mounts_for_additional_signs(self):
        """Report additional signs with non-existing mount references"""
        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS",
            "results": list(
                map(
                    lambda x: {"additional_sign_source_id": x[0], "mount_source_id": x[1]},
                    self.no_mounts_per_additional_sign_id.items(),
                )
            ),
        }

    def _get_mount_distances(self):
        """Report distances from mounts to attached signs"""
        distances = {}
        results = []
        for mount_id, data_d in self.mounts_by_id.items():
            distances[mount_id] = {}
            distances[mount_id]["additional_signs"] = self._get_distances_for_mount(data_d, "additional_signs")
            distances[mount_id]["signs"] = self._get_distances_for_mount(data_d, "signs")
            results.append({"mount_source_id": mount_id, "distance": distances[mount_id]})

        return {"REPORT_TYPE": "MOUNT DISTANCES", "results": results}

    @staticmethod
    def _get_distances_for_mount(mount_data, objects_field_name):
        """Helper to calculate distances for mount"""
        distances = {}
        for entry in mount_data[objects_field_name]:
            distances.setdefault(entry[CSVHeadersV2.id], []).append(entry["distance_to_mount"])
        return [{"mount_source_id": mount_data[CSVHeadersV2.id], "distances": distances}]

    def _get_sign_distances(self):
        """Report distances from signs to mounts"""
        results = map(
            lambda x: {
                "sign_source_id": x.get(CSVHeadersV2.id),
                "sign_code": x.get(CSVHeadersV2.code),
                "mount_source_id": x.get(CSVHeadersV2.mount_id),
                "mount_type": self._get_mount_type(x.get(CSVHeadersV2.mount_id)),
                "distance_to_mount": x.get("distance_to_mount"),
                "status": x.get(CSVHeadersV2.status),
                "link": x.get(CSVHeadersV2.attachment_url),
            },
            filter(lambda x: x.get(CSVHeadersV2.id) not in self.no_mounts_per_sign_id, self.signs_by_id.values()),
        )
        return {"REPORT_TYPE": "SIGN DISTANCES", "results": list(results)}

    def _get_additional_sign_distances(self):
        """Report distances from additional signs to mounts and parent signs"""
        results = map(
            lambda x: {
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
            },
            filter(
                lambda x: x.get(CSVHeadersV2.id) not in self.no_mounts_per_additional_sign_id,
                self.additional_signs_by_id.values(),
            ),
        )
        return {"REPORT_TYPE": "ADDITIONAL SIGN DISTANCES", "results": list(results)}

    def _get_mountless_signs(self):
        """Report signs without mount references"""
        return {
            "REPORT_TYPE": "MOUNTLESS SIGNS",
            "results": list(
                map(
                    lambda x: {"sign_source_id": x.get(CSVHeadersV2.id)},
                    filter(lambda x: not x[CSVHeadersV2.mount_id].strip(), self.signs_by_id.values()),
                )
            ),
        }

    def _get_mountless_additional_signs(self):
        """Report additional signs without mount references"""
        return {
            "REPORT_TYPE": "MOUNTLESS ADDITIONAL SIGNS",
            "results": list(
                map(
                    lambda x: {"additional_sign_source_id": x.get(CSVHeadersV2.id)},
                    filter(lambda x: not x[CSVHeadersV2.mount_id].strip(), self.additional_signs_by_id.values()),
                )
            ),
        }

    def _get_signless_additional_signs(self):
        """Report additional signs without parent sign references"""
        results = []
        for obj in filter(lambda x: not x[CSVHeadersV2.parent_sign_id].strip(), self.additional_signs_by_id.values()):
            source_id = obj.get(CSVHeadersV2.id)
            results.append(
                {
                    "additional_sign_source_id": source_id,
                    "old_device_code": self.additional_sign_reals_by_source_id.get(source_id),
                    "new_device_code": obj.get(CSVHeadersV2.code),
                    "status": obj.get(CSVHeadersV2.status),
                }
            )
        return {
            "REPORT_TYPE": "SIGNLESS ADDITIONAL SIGNS",
            "results": results,
        }

    def _get_mount_type(self, mount_id):
        """Get mount type for a given mount ID"""
        mount = self.mounts_by_id.get(mount_id)
        return mount.get(CSVHeadersV2.mount_type) if mount else None

    # ==================== CSV Preprocessing Reports ====================

    def _get_filtered_signs_report(self) -> dict[str, Any]:
        """Report sign rows that were filtered out during CSV reading.

        This report shows rows that were removed from processing because they had
        invalid device type codes (e.g., "x" or "not classified").

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {
            "REPORT_TYPE": "FILTERED SIGNS (REMOVED FROM CSV)",
            "results": self.filtered_signs,
        }

    def _get_enriched_signs_report(self) -> dict[str, Any]:
        """Report sign rows that had location_specifier values added.

        This report shows rows that were enriched with location_specifier=4 based on
        their device type code. These codes require a specific location specifier value.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {
            "REPORT_TYPE": "ENRICHED SIGNS (LOCATION_SPECIFIER ADDED)",
            "results": self.enriched_signs,
        }

    # ==================== New Status-Based Reports ====================

    def _get_status_distribution_report(self):
        """Report count and percentage of objects by status"""

        def get_stats(objects_by_status, object_type):
            total = sum(len(objects) for objects in objects_by_status.values())
            stats = []
            for status, objects in objects_by_status.items():
                count = len(objects)
                percentage = (count / total * 100) if total > 0 else 0

                # Breakdown by device type code for signs
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
        """Report objects with invalid status values"""
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
                Must match keys in mounts_by_status, signs_by_status, etc.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                For signs, includes old_device_code, new_device_code, and has_changed fields.
        """
        results = []

        # Report mounts with specified status
        for obj in self.mounts_by_status.get(status, []):
            results.append(
                {
                    "object_type": "mount",
                    "source_id": obj.get(CSVHeadersV2.id),
                    "mount_type": obj.get(CSVHeadersV2.mount_type),
                }
            )

        # Report traffic signs with specified status
        results.extend(
            self._get_sign_status_records(
                self.signs_by_status.get(status, []),
                self.sign_reals_by_source_id,
                "traffic_sign",
            )
        )

        # Report additional signs with specified status
        results.extend(
            self._get_sign_status_records(
                self.additional_signs_by_status.get(status, []),
                self.additional_sign_reals_by_source_id,
                "additional_sign",
            )
        )

        report_type = f"{status.upper()} RECORDS"
        return {"REPORT_TYPE": report_type, "results": results}

    @staticmethod
    def _get_sign_status_records(
        sign_objects: list, db_codes_mapping: dict[str, str | None], object_type: str
    ) -> list[dict[str, Any]]:
        """Helper method to generate status records for signs (traffic or additional).

        Args:
            sign_objects (list): List of sign objects from CSV.
            db_codes_mapping (dict[str, str | None]): Mapping of source_id to device_type code from database.
            object_type (str): Type of object ("traffic_sign" or "additional_sign").

        Returns:
            list[dict[str, Any]]: List of sign record dictionaries.
        """
        results = []
        for obj in sign_objects:
            source_id = obj.get(CSVHeadersV2.id)
            old_device_code = db_codes_mapping.get(source_id)
            new_device_code = obj.get(CSVHeadersV2.code)
            results.append(
                {
                    "object_type": object_type,
                    "source_id": source_id,
                    "old_device_code": old_device_code,
                    "new_device_code": new_device_code,
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

    def _get_remove_records_report(self):
        """Report all records with status=Removed"""
        results = []

        for obj in self.mounts_by_status["Removed"]:
            results.append(
                {
                    "object_type": "mount",
                    "mount_source_id": obj.get(CSVHeadersV2.id),
                }
            )

        for obj in self.signs_by_status["Removed"]:
            results.append(
                {
                    "object_type": "traffic_sign",
                    "sign_source_id": obj.get(CSVHeadersV2.id),
                    "device_code": obj.get(CSVHeadersV2.code),
                }
            )

        for obj in self.additional_signs_by_status["Removed"]:
            results.append(
                {
                    "object_type": "additional_sign",
                    "additional_sign_source_id": obj.get(CSVHeadersV2.id),
                    "device_code": obj.get(CSVHeadersV2.code),
                }
            )

        return {"REPORT_TYPE": "REMOVE RECORDS", "results": results}

    def _get_remove_with_invalid_location_report(self):
        """Report Removed status records with invalid locations"""
        results = []

        for obj in self.mounts_by_status["Removed"]:
            location = Point(
                float(obj[CSVHeadersV2.coord_x]),
                float(obj[CSVHeadersV2.coord_y]),
                float(obj[CSVHeadersV2.coord_z]),
                srid=settings.SRID,
            )
            if not geometry_is_legit(location):
                results.append(
                    {
                        "object_type": "mount",
                        "mount_source_id": obj.get(CSVHeadersV2.id),
                        "location": location.ewkt,
                    }
                )

        for obj in self.signs_by_status["Removed"]:
            location = Point(
                float(obj[CSVHeadersV2.coord_x]),
                float(obj[CSVHeadersV2.coord_y]),
                float(obj[CSVHeadersV2.coord_z]),
                srid=settings.SRID,
            )
            if not geometry_is_legit(location):
                results.append(
                    {
                        "object_type": "traffic_sign",
                        "sign_source_id": obj.get(CSVHeadersV2.id),
                        "device_code": obj.get(CSVHeadersV2.code),
                        "location": location.ewkt,
                    }
                )

        for obj in self.additional_signs_by_status["Removed"]:
            location = Point(
                float(obj[CSVHeadersV2.coord_x]),
                float(obj[CSVHeadersV2.coord_y]),
                float(obj[CSVHeadersV2.coord_z]),
                srid=settings.SRID,
            )
            if not geometry_is_legit(location):
                results.append(
                    {
                        "object_type": "additional_sign",
                        "additional_sign_source_id": obj.get(CSVHeadersV2.id),
                        "device_code": obj.get(CSVHeadersV2.code),
                        "location": location.ewkt,
                    }
                )

        return {"REPORT_TYPE": "REMOVE WITH INVALID LOCATION", "results": results}

    @staticmethod
    def _get_sign_scanned_at(date_str):
        """Need to add 00 to the end as source date has only +00 as tz marker"""
        return datetime.strptime(date_str + "00", "%Y/%m/%d %H:%M:%S%z")

    def _get_timestamp_format_validation_report(self):
        """Report records with invalid timestamp formats"""
        results = []

        def validate_timestamp(obj, object_type):
            timestamp_str = obj.get(CSVHeadersV2.scanned_at, "")
            if not timestamp_str:
                return None

            try:
                # Try to parse timestamp (assuming ISO format or similar)
                self._get_sign_scanned_at(timestamp_str)

            except (ValueError, AttributeError):
                if object_type == "mount":
                    id_field = "mount_source_id"
                elif object_type == "traffic_sign":
                    id_field = "sign_source_id"
                else:  # additional_sign
                    id_field = "additional_sign_source_id"

                return {
                    "object_type": object_type,
                    id_field: obj.get(CSVHeadersV2.id),
                    "invalid_timestamp": timestamp_str,
                }
            return None

        # Check all objects
        for obj in self.mounts_by_id.values():
            if error := validate_timestamp(obj, "mount"):
                results.append(error)

        for obj in self.signs_by_id.values():
            if error := validate_timestamp(obj, "traffic_sign"):
                results.append(error)

        for obj in self.additional_signs_by_id.values():
            if error := validate_timestamp(obj, "additional_sign"):
                results.append(error)

        return {"REPORT_TYPE": "TIMESTAMP FORMAT ERRORS", "results": results}

    def _get_invalid_device_type_codes_report(self) -> dict[str, Any]:
        """Report device type codes found in CSV that don't exist in the database.

        This report identifies signs (both traffic signs and additional signs) that have
        device type codes not found in the TrafficControlDeviceType table. These codes
        are invalid and the signs will be skipped during import.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains object_type, source_id, and invalid_code.
        """
        results = []
        seen_codes = set()

        # Check traffic signs
        for source_id, sign_data in self.signs_by_id.items():
            code = sign_data.get(CSVHeadersV2.code, "").strip()
            if code and code not in self.code_to_device_type_id:
                if code not in seen_codes:
                    seen_codes.add(code)
                results.append(
                    {
                        "object_type": "traffic_sign",
                        "sign_source_id": source_id,
                        "invalid_code": code,
                        "status": sign_data.get(CSVHeadersV2.status),
                    }
                )

        # Check additional signs
        for source_id, sign_data in self.additional_signs_by_id.items():
            code = sign_data.get(CSVHeadersV2.code, "").strip()
            if code and code not in self.code_to_device_type_id:
                if code not in seen_codes:
                    seen_codes.add(code)
                results.append(
                    {
                        "object_type": "additional_sign",
                        "additional_sign_source_id": source_id,
                        "invalid_code": code,
                        "status": sign_data.get(CSVHeadersV2.status),
                    }
                )

        return {"REPORT_TYPE": "INVALID DEVICE TYPE CODES", "results": results}

    def _get_missing_mounts_from_database_report(self) -> dict[str, Any]:
        """Report mounts with non-New status that don't exist in the database.

        Mounts with status 'Unchanged', 'Changed', or 'Removed' should already exist
        in the database. This report identifies mounts that violate this expectation.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        non_new_statuses = ["Unchanged", "Changed", "Removed"]

        for status in non_new_statuses:
            for obj in self.mounts_by_status[status]:
                source_id = obj.get(CSVHeadersV2.id)
                if source_id not in self.mount_reals_by_source_id_set:
                    # Collect device type codes from attached signs
                    traffic_sign_codes = [
                        sign.get(CSVHeadersV2.code, "").strip()
                        for sign in obj.get("signs", [])
                        if sign.get(CSVHeadersV2.code, "").strip()
                    ]
                    additional_sign_codes = [
                        sign.get(CSVHeadersV2.code, "").strip()
                        for sign in obj.get("additional_signs", [])
                        if sign.get(CSVHeadersV2.code, "").strip()
                    ]

                    results.append(
                        {
                            "mount_source_id": source_id,
                            "status": status,
                            "mount_type": obj.get(CSVHeadersV2.mount_type),
                            "traffic_sign_codes": ", ".join(traffic_sign_codes) if traffic_sign_codes else "",
                            "additional_sign_codes": ", ".join(additional_sign_codes) if additional_sign_codes else "",
                            "is_orphan": not traffic_sign_codes and not additional_sign_codes,
                        }
                    )

        return {"REPORT_TYPE": "MISSING MOUNTS FROM DATABASE", "results": results}

    def _get_missing_traffic_signs_from_database_report(self) -> dict[str, Any]:
        """Report traffic signs with non-New status that don't exist in the database.

        Traffic signs with status 'Unchanged', 'Changed', or 'Removed' should already exist
        in the database. This report identifies signs that violate this expectation.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        non_new_statuses = ["Unchanged", "Changed", "Removed"]

        for status in non_new_statuses:
            for obj in self.signs_by_status[status]:
                source_id = obj.get(CSVHeadersV2.id)
                if source_id not in self.sign_reals_by_source_id:
                    results.append(
                        {
                            "sign_source_id": source_id,
                            "status": status,
                            "device_code": obj.get(CSVHeadersV2.code),
                        }
                    )

        return {"REPORT_TYPE": "MISSING TRAFFIC SIGNS FROM DATABASE", "results": results}

    def _get_missing_additional_signs_from_database_report(self) -> dict[str, Any]:
        """Report additional signs with non-New status that don't exist in the database.

        Additional signs with status 'Unchanged', 'Changed', or 'Removed' should already exist
        in the database. This report identifies signs that violate this expectation.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        non_new_statuses = ["Unchanged", "Changed", "Removed"]

        for status in non_new_statuses:
            for obj in self.additional_signs_by_status[status]:
                source_id = obj.get(CSVHeadersV2.id)
                if source_id not in self.additional_sign_reals_by_source_id:
                    results.append(
                        {
                            "additional_sign_source_id": source_id,
                            "status": status,
                            "device_code": obj.get(CSVHeadersV2.code),
                        }
                    )

        return {"REPORT_TYPE": "MISSING ADDITIONAL SIGNS FROM DATABASE", "results": results}

    # ==================== New Duplicate Detection Reports ====================

    def _get_duplicate_signs_on_same_mount(self, exact_code_match: bool = False) -> dict[str, Any]:
        """Report multiple signs on same mount with same device type or exact code.

        Args:
            exact_code_match (bool): If True, only match signs with exact same code.
                If False, match signs with same device type ID (considers legacy codes).
                Defaults to False.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains mount_source_id, mount_location, and duplicate_signs list.
                Each duplicate sign is formatted as: "source_id | device_code | status"
        """
        results = []

        for mount_id, signs in self.signs_by_mount_id.items():
            # Group signs by either exact code or device type ID
            grouped = {}
            for sign in signs:
                code = sign.get(CSVHeadersV2.code)

                # Skip signs with codes that don't map to a valid device type
                if not code or code not in self.code_to_device_type_id:
                    continue

                if exact_code_match:
                    # Group by exact code string
                    key = code
                else:
                    # Group by device type ID (considers legacy codes)
                    key = self.code_to_device_type_id.get(code)

                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(sign)

            # Report duplicates
            for key, sign_list in grouped.items():
                if len(sign_list) >= 2:
                    # Get mount location
                    mount_data = self.mounts_by_id.get(mount_id)
                    mount_location = None
                    if mount_data:
                        location = Point(
                            float(mount_data[CSVHeadersV2.coord_x]),
                            float(mount_data[CSVHeadersV2.coord_y]),
                            float(mount_data[CSVHeadersV2.coord_z]),
                            srid=settings.SRID,
                        )
                        mount_location = location.ewkt

                    # Format duplicate signs information
                    duplicate_signs = []
                    for sign in sign_list:
                        sign_info = (
                            f"{sign.get(CSVHeadersV2.id)} | "
                            f"{sign.get(CSVHeadersV2.code)} | "
                            f"{sign.get(CSVHeadersV2.status)}"
                        )
                        duplicate_signs.append(sign_info)

                    result = {
                        "mount_source_id": mount_id,
                        "mount_location": mount_location,
                        "duplicate_signs": duplicate_signs,
                    }
                    results.append(result)

        report_type = (
            "DUPLICATE SIGNS ON SAME MOUNT (EXACT CODE)" if exact_code_match else "DUPLICATE SIGNS ON SAME MOUNT"
        )
        return {"REPORT_TYPE": report_type, "results": results}

    def _get_duplicate_signs_on_same_mount_by_device_type(self) -> dict[str, Any]:
        """Report multiple signs on same mount with same device type (considering legacy codes).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_duplicate_signs_on_same_mount(exact_code_match=False)

    def _get_duplicate_signs_on_same_mount_exact_code(self) -> dict[str, Any]:
        """Report multiple signs on same mount with exact same code (no legacy code matching).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return self._get_duplicate_signs_on_same_mount(exact_code_match=True)

    def _get_added_double_sided_zebra_crossings(self) -> dict[str, Any]:
        """Report new zebra crossing signs that are double-sided (180° apart).

        Only analyzes signs with status='New'. Zebra crossing signs are identified by codes:
        - Left: 511, 5112, E1_2
        - Right: 5111, E1

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []

        for mount_id, signs in self.signs_by_mount_id.items():
            # Filter for New status zebra crossing signs
            zebra_signs = [
                sign
                for sign in signs
                if sign.get(CSVHeadersV2.status) == "New" and sign.get(CSVHeadersV2.code) in ZEBRA_CROSSING_ALL_CODES
            ]

            # Need at least 2 signs to be double-sided
            if len(zebra_signs) < 2:
                continue

            # Check pairs of zebra crossing signs
            for i, sign1 in enumerate(zebra_signs):
                for sign2 in zebra_signs[i + 1 :]:
                    code1 = sign1.get(CSVHeadersV2.code)
                    code2 = sign2.get(CSVHeadersV2.code)

                    # Check if they have opposing directions
                    try:
                        dir1 = int(sign1.get(CSVHeadersV2.direction, 0))
                        dir2 = int(sign2.get(CSVHeadersV2.direction, 0))

                        # Calculate direction difference
                        diff = abs(dir1 - dir2)
                        # Normalize to 0-180 range
                        if diff > 180:
                            diff = 360 - diff

                        # Check if approximately 180° apart (within tolerance)
                        if abs(diff - 180) <= DIRECTION_TOLERANCE:
                            results.append(
                                {
                                    "mount_source_id": mount_id,
                                    "sign_source_ids": [sign1.get(CSVHeadersV2.id), sign2.get(CSVHeadersV2.id)],
                                    "codes_found": [code1, code2],
                                    "directions": [dir1, dir2],
                                    "direction_difference": diff,
                                    "status": "New",
                                }
                            )
                    except (ValueError, TypeError):
                        # Skip if direction values are invalid
                        pass

        return {"REPORT_TYPE": "ADDED DOUBLE SIDED ZEBRA CROSSINGS", "results": results}

    # ==================== Sanity Check Reports ====================

    def _get_mounts_found_in_database_report(self) -> dict[str, Any]:
        """Report all mounts from CSV that exist in the database with source_id to db_id mapping.

        This sanity check report lists all mounts that are found in both CSV and database,
        showing the mapping between source_id (from CSV) and db_id (from database).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []

        for source_id, mount_data in self.mounts_by_id.items():
            db_id = self.mount_source_id_to_db_id.get(source_id)
            if db_id:
                results.append(
                    {
                        "source_id": source_id,
                        "db_id": str(db_id),
                        "status": mount_data.get(CSVHeadersV2.status),
                    }
                )

        return {"REPORT_TYPE": "MOUNTS FOUND IN DATABASE", "results": results}

    def _get_traffic_signs_found_in_database_report(self) -> dict[str, Any]:
        """Report all traffic signs from CSV that exist in the database with source_id to db_id mapping.

        This sanity check report lists all traffic signs that are found in both CSV and database,
        showing the mapping between source_id (from CSV) and db_id (from database).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []

        for source_id, sign_data in self.signs_by_id.items():
            db_id = self.sign_source_id_to_db_id.get(source_id)
            if db_id:
                results.append(
                    {
                        "source_id": source_id,
                        "db_id": str(db_id),
                        "status": sign_data.get(CSVHeadersV2.status),
                    }
                )

        return {"REPORT_TYPE": "TRAFFIC SIGNS FOUND IN DATABASE", "results": results}

    def _get_additional_signs_found_in_database_report(self) -> dict[str, Any]:
        """Report all additional signs from CSV that exist in the database with source_id to db_id mapping.

        This sanity check report lists all additional signs that are found in both CSV and database,
        showing the mapping between source_id (from CSV) and db_id (from database).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []

        for source_id, sign_data in self.additional_signs_by_id.items():
            db_id = self.additional_sign_source_id_to_db_id.get(source_id)
            if db_id:
                results.append(
                    {
                        "source_id": source_id,
                        "db_id": str(db_id),
                        "status": sign_data.get(CSVHeadersV2.status),
                    }
                )

        return {"REPORT_TYPE": "ADDITIONAL SIGNS FOUND IN DATABASE", "results": results}

    def _get_main_signs_with_parent_report(self) -> dict[str, Any]:
        """Report main traffic signs (not additional signs) that have a parent sign reference.

        Main traffic signs typically should not have a parent sign - this is usually only for
        additional signs. This report identifies potentially incorrect data where a main sign
        references a parent sign.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []

        for source_id, sign_data in self.signs_by_id.items():
            parent_source_id = sign_data.get(CSVHeadersV2.parent_sign_id, "").strip()

            if parent_source_id:
                # This main sign has a parent reference
                sign_code = sign_data.get(CSVHeadersV2.code)

                # Check if parent is a main sign or additional sign
                parent_is_additional = parent_source_id in self.additional_signs_by_id
                parent_is_main_sign = parent_source_id in self.signs_by_id

                if parent_is_additional:
                    parent_data = self.additional_signs_by_id[parent_source_id]
                    parent_type = "additional_sign"
                elif parent_is_main_sign:
                    parent_data = self.signs_by_id[parent_source_id]
                    parent_type = "main_sign"
                else:
                    # Parent not found in CSV
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

    def _get_mounts_with_removed_signs_report(self) -> dict[str, Any]:
        """Report mounts that have at least one removed sign (main or additional).

        This report identifies mounts where any attached sign (either main traffic sign or
        additional sign) has status='Removed'. This helps identify mounts that may need
        inspection or removal.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        results = []
        mounts_with_removed_signs = set()

        # Check main traffic signs with Removed status
        for sign_data in self.signs_by_status["Removed"]:
            mount_source_id = sign_data.get(CSVHeadersV2.mount_id, "").strip()
            if mount_source_id:
                mounts_with_removed_signs.add(mount_source_id)

        # Check additional signs with Removed status
        for sign_data in self.additional_signs_by_status["Removed"]:
            mount_source_id = sign_data.get(CSVHeadersV2.mount_id, "").strip()
            if mount_source_id:
                mounts_with_removed_signs.add(mount_source_id)

        # Build results with mount details
        for mount_source_id in mounts_with_removed_signs:
            mount_data = self.mounts_by_id.get(mount_source_id)
            if mount_data:
                location = Point(
                    float(mount_data[CSVHeadersV2.coord_x]),
                    float(mount_data[CSVHeadersV2.coord_y]),
                    float(mount_data[CSVHeadersV2.coord_z]),
                    srid=settings.SRID,
                )
                results.append(
                    {
                        "mount_source_id": mount_source_id,
                        "location": location.ewkt,
                    }
                )

        return {"REPORT_TYPE": "MOUNTS WITH REMOVED SIGNS", "results": results}
