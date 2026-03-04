import csv
import os
import re
from datetime import datetime
from typing import Any, Callable

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

# Compiled regex pattern for extracting numeric part from number_code field
NUMBER_CODE_PATTERN = re.compile(r'^(\d+)')

# Code transformation configuration constants
INVALID_CODES = {"x", "not classified", "k06"}  # Codes that should be filtered out (case insensitive)

# Direct code-to-code replacement mappings
CODE_REPLACEMENTS = {
    "331": "3311",
    "373": "3732",
    "374": "3742",
    "411": "4111",
    "411_2": "4112",
    "413": "4131",
    "413_2": "4132",
    "413_3": "4133",
    "413_4": "4134",
    "413_5": "4135",
    "413_6": "4136",
    "414": "4141",
    "414_2": "4142",
    "414_4": "4144",
    "417": "4171",
    "417_2": "4172",
    "511": "5111",
    "511_2": "5112",
    "520_1": "5201",
    "521a": "52111",
    "521b": "52151",
    "521c": "52131",
    "531": "5311",
    "532": "5321",
    "533": "5331",
    "541a": "5411",
    "541b": "5412",
    "542b": "5422",
    "543a": "5431",
    "551": "5511",
    "551_2": "5512",
    "571": "5711",
    "572": "5721",
    "622": "6221",
    "623_2": "62324",
    "650": "6501",
    "650_2": "6502",
    "650_3": "6504",
    "651": "6511",
    "651_2": "6512",
    "681":"833S",
    "681_2":"831S",
    "681_3":"832S",
    "681_4":"834S",
    "681_5":"841S",
    "681_8":"6818",
    "681_9":"6819",
    "821": "821K",
    "823": "823K",
    "827": "827K",
    "863": "8631",
    "871": "87111",
    "871_5": "87115",
    "872": "8722K",
    "872_2": "8714K",
    "931-1": "9311",
    "E4.3_4": "E4.3_3_2_1",
    "H11S": "H11.1",
    "H12.8_2": "12.8",
    "H12.10_4": "H12.10_2_2",
    "H19.2_2S": "H19.2_2",
    "H19.2_3S": "H19.2_3",
    "H19.2_4S": "H19.2_4",
    "H20.1": "H20_4",
    "H20.1S": "H20_4S",
}

# Codes that require color-based suffix (K for color=2, S for color=1)
COLOR_DEPENDENT_CODES = {
    "814", "815", "824", "825", "826", "827", "828",
    "831", "832", "833", "833_2", "834", "836",
    "843", "845", "851", "852", "853", "H12.10_4_2"
}

# Codes that should get a default 'K' suffix if color field is missing from CSV
COLOR_CODES_WITH_DEFAULT_SUFFIX = {"825", "826", "828"}

# Codes that require both code mapping AND color-based suffix
# Format: old_code -> {"new_code": "replacement", "color_1_suffix": "S/K/None", "color_2_suffix": "S/K/None"}
# If suffix is None, no suffix is added for that color value
CODE_AND_COLOR_DEPENDENT_CODES = {
    "H19_3": {"new_code": "H19.1_2", "color_1_suffix": "S", "color_2_suffix": None},
    "853_2": {"new_code": "8531", "color_1_suffix": "S", "color_2_suffix": "K"},
    "854": {"new_code": "8541", "color_1_suffix": "S", "color_2_suffix": "K"},
    "854_2": {"new_code": "8543", "color_1_suffix": "S", "color_2_suffix": "K"},
    "855a": {"new_code": "8552", "color_1_suffix": "S", "color_2_suffix": "K"},
    "855b": {"new_code": "8552", "color_1_suffix": "S", "color_2_suffix": "K"},
    "856a": {"new_code": "8561", "color_1_suffix": "S", "color_2_suffix": "K"},
    "856b": {"new_code": "8561", "color_1_suffix": "S", "color_2_suffix": "K"},
    "861b": {"new_code": "H22.2_6", "color_1_suffix": "S", "color_2_suffix": "K"},
    "H12.10_2": {"new_code": "H12.10_2_2", "color_1_suffix": "S", "color_2_suffix": "K"},
    "H12.2_2": {"new_code": "H12.2_2_2", "color_1_suffix": "S", "color_2_suffix": "K"},
    # Codes with conditional suffix only (no code mapping)
    "845": {"new_code": "845", "color_1_suffix": None, "color_2_suffix": "K"},
    "833_2": {"new_code": "833_2", "color_1_suffix": "S", "color_2_suffix": None},
    "H12.10_2_2": {"new_code": "H12.10_2_2", "color_1_suffix": "S", "color_2_suffix": None},
}

# Codes that should be replaced with validation against number_code field
# Format: old_code -> {"expected_number": "value", "new_code": "replacement"}
NUMBER_CODE_DEPENDENT_CODES = {
    "344_12": {"expected_number": "12", "new_code": "344"},
    "344_30": {"expected_number": "30", "new_code": "344"},
    "344_6": {"expected_number": "6", "new_code": "344"},
    "344_8": {"expected_number": "8", "new_code": "344"},
    "345_60": {"expected_number": "60", "new_code": "345"},
    "346_10": {"expected_number": "10", "new_code": "346"},
    "346_8": {"expected_number": "8", "new_code": "346"},
    "347_16": {"expected_number": "16", "new_code": "347"},
    "347_18": {"expected_number": "18", "new_code": "347"},
    "347_21": {"expected_number": "21", "new_code": "347"},
    "361_10": {"expected_number": "10", "new_code": "361"},
    "361_20": {"expected_number": "20", "new_code": "3619"},
    "361_30": {"expected_number": "30", "new_code": "3617"},
    "361_40": {"expected_number": "40", "new_code": "3618"},
    "361_5": {"expected_number": "5", "new_code": "361"},
    "361_50": {"expected_number": "50", "new_code": "3611"},
    "361_60": {"expected_number": "60", "new_code": "3612"},
    "361_70": {"expected_number": "70", "new_code": "3613"},
    "361_80": {"expected_number": "80", "new_code": "3614"},
    "362_20": {"expected_number": "20", "new_code": "362"},
    "362_30": {"expected_number": "30", "new_code": "3622"},
    "363_20": {"expected_number": "20", "new_code": "3637"},
    "363_30": {"expected_number": "30", "new_code": "3634"},
    "363_40": {"expected_number": "40", "new_code": "3635"},
    "364_20": {"expected_number": "20", "new_code": "3647"},
    "364_30": {"expected_number": "30", "new_code": "3644"},
    "364_40": {"expected_number": "40", "new_code": "3646"},
}

# Conditional code replacements based on number_code value
# Format: code -> {number_value: new_code}
# Only replaces if number_code matches a key, otherwise code stays unchanged
CONDITIONAL_NUMBER_CODE_REPLACEMENTS = {
    "363": {"40": "3635"},
}

# Enrichment texts for internal_additional_info field based on device type code
INTERNAL_ADDITIONAL_INFO_ENRICHMENTS = {
    "833S": "lisäksi voi olla lisäkilpi 832S linja-auto",
    "831S": "voi olla lisäkilpi 834S pakettiauto tai 833S kuorma-auto",
    "832S": "tai merkki 5411 linja-autokaista",
    "834S": "tai lisäkilpi 833S kuorma-auto",
    "6819": "tai lisäkilpi 843S polkypyörä",
}

# Codes that should have location_specifier = 4
LOCATION_SPECIFIER_4_CODES = [
    "4171", "4172", "418",
    "D3.1", "D3.1_2",
    "D3.2", "D3.2_2",
    "D3.3", "D3.3_2"
]


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
            previous_mount_file (str | None): Path to the previous mount CSV file for tracking source_ids.
                Defaults to None.
            previous_sign_file (str | None): Path to the previous sign CSV file for tracking source_ids.
                Defaults to None.
            delimiter (str): CSV delimiter character. Defaults to ",".
        """
        self.delimiter = delimiter

        # Read CSV files into memory once at initialization
        self.mount_rows = self._read_csv_file(mount_file, delimiter)
        self.sign_rows = self._read_csv_file(sign_file, delimiter)

        # Read previous CSV files if provided - use semicolon delimiter
        if previous_mount_file:
            self.previous_mount_rows = self._read_csv_file(previous_mount_file, ";")
        else:
            self.previous_mount_rows = []

        if previous_sign_file:
            self.previous_sign_rows = self._read_csv_file(previous_sign_file, ";")
        else:
            self.previous_sign_rows = []

        # Build sets of source IDs from previous import for comparison
        self.old_mount_source_ids = self._build_source_id_set(self.previous_mount_rows)
        self.old_sign_source_ids = self._build_source_id_set(self.previous_sign_rows)

        # Initialize tracking for filtering and enrichment
        self.filtered_signs = []  # Rows removed due to invalid codes
        self.enriched_signs = []  # Rows that had location_specifier added
        self.code_replacements = []  # Rows that had device type code replaced
        self.code_replacement_failures = []  # Rows where code replacement failed sanity checks

        # Add internal_additional_info field BEFORE filtering/enrichment so pipeline can populate it
        self._add_internal_additional_info_to_rows(self.sign_rows)

        # Filter and enrich sign rows
        self.sign_rows = self._filter_and_enrich_sign_rows(self.sign_rows)

        # Build DB source_id -> device_type.code maps BEFORE saving CSV (needed for internal_status)
        self.sign_reals_by_source_id = self._build_sign_reals_by_source_id()
        self.additional_sign_reals_by_source_id = self._build_additional_sign_reals_by_source_id()

        # Add internal_status to each row based on database comparison
        self._add_internal_status_to_rows(self.sign_rows)


        # Save filtered CSV to same folder as input file with timestamp
        self._save_filtered_csv(sign_file, self.sign_rows, delimiter)

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
        # Note: sign_reals_by_source_id and additional_sign_reals_by_source_id already built earlier for internal_status

        # Build DB source_id -> legacy_code maps for change record comparison
        self.sign_reals_legacy_codes_by_source_id = self._build_sign_reals_legacy_codes_by_source_id()
        self.additional_sign_reals_legacy_codes_by_source_id = (
            self._build_additional_sign_reals_legacy_codes_by_source_id()
        )

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
            self._get_code_replacements_report(),
            self._get_code_replacement_failures_report(),
            # New status-based reports
            self._get_status_distribution_report(),
            self._get_invalid_status_report(),
            self._get_change_records_report(),
            self._get_unchanged_records_report(),
            self._get_new_records_report(),
            self._get_remove_records_report(),
            self._get_remove_with_invalid_location_report(),
            self._get_timestamp_format_validation_report(),
            self._get_invalid_device_type_codes_report(),
            self._get_status_internal_status_mismatch_report(),
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

    @staticmethod
    def _read_csv_file(csv_file_path: str, delimiter: str) -> list[dict]:
        """Read CSV file into memory with specified delimiter.

        Args:
            csv_file_path (str): Path to the CSV file.
            delimiter (str): CSV delimiter character to use.

        Returns:
            list[dict]: List of dictionaries representing CSV rows.
        """
        rows = []
        with open(csv_file_path) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
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

    @staticmethod
    def _save_filtered_csv(original_file_path: str, filtered_rows: list[dict], delimiter: str) -> None:
        """Save filtered and enriched sign data to CSV file.

        Creates a new CSV file in the same directory as the original file with
        suffix '_filtered_<timestamp>' added to the filename.

        Args:
            original_file_path (str): Path to the original CSV file.
            filtered_rows (list[dict]): Filtered and enriched sign rows to save.
            delimiter (str): CSV delimiter character to use.
        """
        if not filtered_rows:
            print(f"All entries have been filtered out. No CSV saved")
            return

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = os.path.dirname(original_file_path)
        basename = os.path.basename(original_file_path)
        name_without_ext, ext = os.path.splitext(basename)
        output_filename = f"{name_without_ext}_filtered_{timestamp}{ext}"
        output_path = os.path.join(directory, output_filename)

        # Write filtered data to CSV
        fieldnames = list(filtered_rows[0].keys())
        with open(output_path, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(filtered_rows)

        print(f"Filtered CSV saved to: {output_path}")

    @staticmethod
    def _row_to_csv_line(row: dict, delimiter: str) -> str:
        """Convert a CSV row dictionary back to a CSV line string.

        Args:
            row (dict): Dictionary representing a CSV row.
            delimiter (str): CSV delimiter character to use.

        Returns:
            str: CSV line string with values joined by delimiter.
        """
        # Use csv.writer to properly escape values
        import io
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerow(row.values())
        return output.getvalue().strip()

    def _should_be_filtered(self, row: dict, filter_f: Callable, reason: str) -> bool:
        code = row.get(CSVHeadersV2.code, "").strip()
        if filter_f(code):
            self.filtered_signs.append({
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": reason,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            })
            return True
        return False

    def _apply_direct_code_replacement(self, row: dict) -> str:
        """Apply direct code-to-code replacement if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).

        Returns:
            str: The current code value after potential replacement.
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        if code in CODE_REPLACEMENTS:
            new_code = CODE_REPLACEMENTS[code]
            self.code_replacements.append({
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "direct_mapping",
            })
            row[CSVHeadersV2.code] = new_code
            return new_code
        return code

    def _apply_color_based_suffix(self, row: dict) -> str:
        """Apply color-based suffix transformation if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).

        Returns:
            str: The current code value after potential transformation.
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        if code not in COLOR_DEPENDENT_CODES:
            return code

        color_value = row.get(CSVHeadersV2.color, "").strip()
        has_default_suffix = code in COLOR_CODES_WITH_DEFAULT_SUFFIX

        if not color_value:
            if has_default_suffix:
                suffix = "K"
                new_code = f"{code}{suffix}"
                self.code_replacements.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "old_code": code,
                    "new_code": new_code,
                    "replacement_type": "color_based_default",
                    "color_value": "default_K",
                })
                row[CSVHeadersV2.code] = new_code
                return new_code
            else:
                self.code_replacement_failures.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "code": code,
                    "reason": "missing_color_field",
                    "color_value": color_value,
                    "csv_row": self._row_to_csv_line(row, self.delimiter),
                })
                return code
        elif color_value not in ["1", "2"]:
            self.code_replacement_failures.append({
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": "invalid_color_value",
                "color_value": color_value,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            })
            return code
        else:
            suffix = "S" if color_value == "1" else "K"
            new_code = f"{code}{suffix}"
            self.code_replacements.append({
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "color_based",
                "color_value": color_value,
            })
            row[CSVHeadersV2.code] = new_code
            return new_code

    def _apply_code_and_color_transformation(self, row: dict) -> str:
        """Apply code mapping with color-based suffix transformation if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).

        Returns:
            str: The current code value after potential transformation.
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        if code not in CODE_AND_COLOR_DEPENDENT_CODES:
            return code

        config = CODE_AND_COLOR_DEPENDENT_CODES[code]
        base_code = config["new_code"]
        color_value = row.get(CSVHeadersV2.color, "").strip()

        if not color_value:
            if config["color_1_suffix"] is not None and config["color_2_suffix"] is not None:
                self.code_replacement_failures.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "code": code,
                    "reason": "missing_color_field",
                    "color_value": "missing",
                    "csv_row": self._row_to_csv_line(row, self.delimiter),
                })
                return code
            else:
                new_code = base_code
                self.code_replacements.append({
                    "source_id": row.get(CSVHeadersV2.id),
                    "old_code": code,
                    "new_code": new_code,
                    "replacement_type": "code_and_color_based_no_color",
                    "color_value": "missing",
                    "base_code": base_code,
                    "suffix": "none",
                })
                row[CSVHeadersV2.code] = new_code
                return new_code
        elif color_value not in ["1", "2"]:
            self.code_replacement_failures.append({
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": "invalid_color_value",
                "color_value": color_value,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            })
            return code
        else:
            suffix = config["color_1_suffix"] if color_value == "1" else config["color_2_suffix"]
            new_code = f"{base_code}{suffix}" if suffix else base_code
            self.code_replacements.append({
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "code_and_color_based",
                "color_value": color_value,
                "base_code": base_code,
                "suffix": suffix if suffix else "none",
            })
            row[CSVHeadersV2.code] = new_code
            return new_code

    def _apply_number_code_validation(self, row: dict) -> str:
        """Apply number-code based validation and replacement if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).

        Returns:
            str: The current code value after potential replacement.
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        if code not in NUMBER_CODE_DEPENDENT_CODES:
            return code

        config = NUMBER_CODE_DEPENDENT_CODES[code]
        expected_number = config["expected_number"]
        replacement_code = config["new_code"]
        number_code_value = row.get(CSVHeadersV2.number_code, "").strip()

        # If number_code is not found in CSV, extract from device type code
        if not number_code_value:
            # Extract number from device type code pattern: <code>_<number>
            code_parts = code.split("_")
            if len(code_parts) > 1:
                extracted_number = code_parts[-1]
                # Validate that extracted number matches expected number
                if extracted_number == expected_number:
                    new_code = replacement_code
                    self.code_replacements.append({
                        "source_id": row.get(CSVHeadersV2.id),
                        "old_code": code,
                        "new_code": new_code,
                        "replacement_type": "number_code_based",
                        "number_code_value": f"(extracted from code: {extracted_number})",
                        "validated_number": expected_number,
                    })
                    row[CSVHeadersV2.code] = new_code
                    return new_code
            # If extraction fails or doesn't match, this shouldn't happen based on config
            return code

        # If number_code exists in CSV, validate it matches the expected number
        match = NUMBER_CODE_PATTERN.match(number_code_value)
        cleaned_number = match.group(1) if match else ""

        if cleaned_number != expected_number:
            self.code_replacement_failures.append({
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "reason": "number_code_mismatch",
                "expected_number": expected_number,
                "actual_number_code": number_code_value,
                "cleaned_number": cleaned_number,
                "expected_replacement": replacement_code,
                "csv_row": self._row_to_csv_line(row, self.delimiter),
            })
            return code

        new_code = replacement_code
        self.code_replacements.append({
            "source_id": row.get(CSVHeadersV2.id),
            "old_code": code,
            "new_code": new_code,
            "replacement_type": "number_code_based",
            "number_code_value": number_code_value,
            "validated_number": expected_number,
        })
        row[CSVHeadersV2.code] = new_code
        return new_code

    def _apply_conditional_number_code_replacement(self, row: dict) -> str:
        """Apply conditional code replacement based on number_code value.

        Args:
            row (dict): CSV row dictionary (modified in place).

        Returns:
            str: The current code value after potential replacement.
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        if code not in CONDITIONAL_NUMBER_CODE_REPLACEMENTS:
            return code

        number_code_value = row.get(CSVHeadersV2.number_code, "").strip()

        # Extract numeric part from number_code
        match = NUMBER_CODE_PATTERN.match(number_code_value) if number_code_value else None
        cleaned_number = match.group(1) if match else ""

        # Check if this number has a replacement
        replacements = CONDITIONAL_NUMBER_CODE_REPLACEMENTS[code]
        if cleaned_number in replacements:
            new_code = replacements[cleaned_number]
            self.code_replacements.append({
                "source_id": row.get(CSVHeadersV2.id),
                "old_code": code,
                "new_code": new_code,
                "replacement_type": "conditional_number_code",
            })
            row[CSVHeadersV2.code] = new_code
            return new_code

        return code

    def _enrich_location_specifier(self, row: dict) -> None:
        """Add location_specifier value if applicable.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "").strip()
        location_specifier_value = row.get(CSVHeadersV2.location_specifier, "").strip()

        if not location_specifier_value and code in LOCATION_SPECIFIER_4_CODES:
            self.enriched_signs.append({
                "source_id": row.get(CSVHeadersV2.id),
                "code": code,
                "field": "location_specifier",
                "old_value": location_specifier_value if location_specifier_value else None,
                "new_value": "4",
            })
            row[CSVHeadersV2.location_specifier] = "4"

    def _enrich_internal_additional_info(self, row: dict) -> None:
        """Enrich internal_additional_info field for specific device type codes.

        Args:
            row (dict): CSV row dictionary (modified in place).
        """
        code = row.get(CSVHeadersV2.code, "").strip()

        # Check if code has an enrichment rule
        if code in INTERNAL_ADDITIONAL_INFO_ENRICHMENTS:
            row["internal_additional_info"] = INTERNAL_ADDITIONAL_INFO_ENRICHMENTS[code]

    @staticmethod
    def _is_skipable_code(code: str) -> bool:
        if code[0] == "7":
            return True
        if (code[0] == "6"
            and (
                not code.startswith("62")
                or (not code.startswith("65")))
        ):
            return True
        if (code[0] == "F"
            and (
                not code.startswith("F7.")
                or not code.startswith("F8.")
                or not code.startswith("F18.")
                or not code.startswith("F24")
                or not code.startswith("F51")
                or not code.startswith("F52")
                or not code.startswith("F53")
                or not code.startswith("F54")
                or not code.startswith("F55")
                or not code.startswith("F56")
                or not code.startswith("F57")
            )
        ):
            return True

        return False

    def _filter_and_enrich_sign_rows(self, sign_rows: list[dict]) -> list[dict]:
        """Filter out invalid sign codes, replace device type codes, and add location_specifier values.

        Orchestrates filtering and enrichment pipeline by applying transformations in sequence:
        1. Filter invalid codes ("x", "not classified")
        2. Apply direct code replacements
        3. Apply color-based suffix transformations
        4. Apply code + color dependent transformations
        5. Apply number-code based validation and replacement
        6. Filter skipped codes (after transformations, so replacements can happen first)
        7. Enrich location_specifier field
        8. Enrich internal_additional_info field

        Each transformation delegates to specialized helper methods for reduced complexity.
        Tracks all operations (filtering, replacements, failures, enrichments) for reporting.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries.

        Returns:
            list[dict]: Filtered and enriched list of sign row dictionaries.
        """
        filtered_rows = []

        for row in sign_rows:
            # Step 1: Filter invalid codes (before any transformations)
            if self._should_be_filtered(row, lambda c: c.lower() in INVALID_CODES, "invalid_code"):
                continue

            # Steps 2-5: Apply transformations sequentially
            # Each method modifies row in place and returns updated code for chaining
            self._apply_direct_code_replacement(row)
            self._apply_color_based_suffix(row)
            self._apply_code_and_color_transformation(row)
            self._apply_number_code_validation(row)
            self._apply_conditional_number_code_replacement(row)

            # Step 6: Filter skipped codes (AFTER transformations, so codes like 681->833S work)
            if self._should_be_filtered(row, self._is_skipable_code, "skipped_code"):
                continue

            # Step 7: Enrich location_specifier field
            self._enrich_location_specifier(row)

            # Step 8: Enrich internal_additional_info field
            self._enrich_internal_additional_info(row)

            filtered_rows.append(row)

        return filtered_rows

    def _add_internal_status_to_rows(self, sign_rows: list[dict]) -> None:
        """Add internal_status column to each row based on database comparison.

        Compares each row's device type code with the database entry:
        - "new": Row's source_id doesn't exist in database
        - "unchanged": Row exists in DB and device type code matches
        - "changed": Row exists in DB but device type code is different

        Args:
            sign_rows (list[dict]): List of sign row dictionaries (modified in place).
        """
        for row in sign_rows:
            source_id = row.get(CSVHeadersV2.id, "").strip()
            code = row.get(CSVHeadersV2.code, "").strip()

            if not source_id:
                row["internal_status"] = "new"
                continue

            # Check if it's an additional sign
            is_additional = self._is_additional_sign(row)

            # Get device type code from database
            if is_additional:
                db_code = self.additional_sign_reals_by_source_id.get(source_id)
            else:
                db_code = self.sign_reals_by_source_id.get(source_id)

            # Determine internal_status
            if db_code is None:
                # Not in database
                row["internal_status"] = "new"
            elif db_code == code:
                # Exists in DB and code matches
                row["internal_status"] = "unchanged"
            else:
                # Exists in DB but code is different
                row["internal_status"] = "changed"

    def _add_internal_additional_info_to_rows(self, sign_rows: list[dict]) -> None:
        """Add internal_additional_info field to each row for future enrichment.

        This field is reserved for potential future use and currently will be set to None.

        Args:
            sign_rows (list[dict]): List of sign row dictionaries (modified in place).
        """
        for row in sign_rows:
            row["internal_additional_info"] = None  # Initialize as None for all rows

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
    def _build_sign_reals_legacy_codes_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to legacy_code for active TrafficSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to legacy_code.
        """
        return {
            obj.source_id: obj.legacy_code
            for obj in TrafficSignReal.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).only("source_id", "legacy_code")
        }

    @staticmethod
    def _build_additional_sign_reals_legacy_codes_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to legacy_code for active AdditionalSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to legacy_code.
        """
        return {
            obj.source_id: obj.legacy_code
            for obj in AdditionalSignReal.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).only("source_id", "legacy_code")
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
        """Report signs with non-existing mount references.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains sign_source_id, mount_source_id, devicetypecode,
                status, and internal_status.
        """
        results = []
        for sign_id, mount_id in self.no_mounts_per_sign_id.items():
            sign_data = self.signs_by_id.get(sign_id, {})
            results.append({
                "sign_source_id": sign_id,
                "mount_source_id": mount_id,
                "devicetypecode": sign_data.get(CSVHeadersV2.code, ""),
                "status": sign_data.get(CSVHeadersV2.status, ""),
                "internal_status": sign_data.get("internal_status", ""),
            })

        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR SIGNS",
            "results": results,
        }

    def _get_non_existing_mounts_for_additional_signs(self):
        """Report additional signs with non-existing mount references.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains additional_sign_source_id, mount_source_id,
                devicetypecode, status, and internal_status.
        """
        results = []
        for sign_id, mount_id in self.no_mounts_per_additional_sign_id.items():
            sign_data = self.additional_signs_by_id.get(sign_id, {})
            results.append({
                "additional_sign_source_id": sign_id,
                "mount_source_id": mount_id,
                "devicetypecode": sign_data.get(CSVHeadersV2.code, ""),
                "status": sign_data.get(CSVHeadersV2.status, ""),
                "internal_status": sign_data.get("internal_status", ""),
            })

        return {
            "REPORT_TYPE": "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS",
            "results": results,
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
        """Report additional signs without parent sign references.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains additional_sign_source_id, old_device_code,
                new_device_code, status, and internal_status.
        """
        results = []
        for obj in filter(lambda x: not x[CSVHeadersV2.parent_sign_id].strip(), self.additional_signs_by_id.values()):
            source_id = obj.get(CSVHeadersV2.id)
            results.append(
                {
                    "additional_sign_source_id": source_id,
                    "old_device_code": self.additional_sign_reals_by_source_id.get(source_id),
                    "new_device_code": obj.get(CSVHeadersV2.code),
                    "status": obj.get(CSVHeadersV2.status),
                    "internal_status": obj.get("internal_status", ""),
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

    def _get_code_replacements_report(self) -> dict[str, Any]:
        """Report sign rows that had device type codes replaced.

        This report shows rows where the device type code was replaced according
        to direct mapping rules during preprocessing.

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {
            "REPORT_TYPE": "CODE REPLACEMENTS (DEVICE TYPE CODES UPDATED)",
            "results": self.code_replacements,
        }

    def _get_code_replacement_failures_report(self) -> dict[str, Any]:
        """Report sign rows where code replacement failed sanity checks.

        This report shows rows where conditional code replacement could not be
        performed due to missing or invalid field values (e.g., missing color field).

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
        """
        return {
            "REPORT_TYPE": "CODE REPLACEMENT FAILURES (SANITY CHECK FAILURES)",
            "results": self.code_replacement_failures,
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
                For signs, includes old_device_code, new_device_code, old_legacy_code,
                new_legacy_code, and has_changed fields.
        """
        results = []
        # Report traffic signs with specified status
        results.extend(
            self._get_sign_status_records(
                self.signs_by_status.get(status, []),
                self.sign_reals_by_source_id,
                self.sign_reals_legacy_codes_by_source_id,
                "traffic_sign",
            )
        )

        # Report additional signs with specified status
        results.extend(
            self._get_sign_status_records(
                self.additional_signs_by_status.get(status, []),
                self.additional_sign_reals_by_source_id,
                self.additional_sign_reals_legacy_codes_by_source_id,
                "additional_sign",
            )
        )

        report_type = f"{status.upper()} RECORDS"
        return {"REPORT_TYPE": report_type, "results": results}

    @staticmethod
    def _get_sign_status_records(
        sign_objects: list,
        db_codes_mapping: dict[str, str | None],
        legacy_codes_mapping: dict[str, str | None],
        object_type: str,
    ) -> list[dict[str, Any]]:
        """Helper method to generate status records for signs (traffic or additional).

        Args:
            sign_objects (list): List of sign objects from CSV.
            db_codes_mapping (dict[str, str | None]): Mapping of source_id to device_type code from database.
            legacy_codes_mapping (dict[str, str | None]): Mapping of source_id to legacy_code from database.
            object_type (str): Type of object ("traffic_sign" or "additional_sign").

        Returns:
            list[dict[str, Any]]: List of sign record dictionaries with device codes and legacy codes.
        """
        # TODO Löytyykö databasesta? Löytyykö vanhasta csv-datasta
        results = []
        for obj in sign_objects:
            source_id = obj.get(CSVHeadersV2.id)
            old_device_code = db_codes_mapping.get(source_id)
            new_device_code = obj.get(CSVHeadersV2.code)
            old_legacy_code = legacy_codes_mapping.get(source_id)
            new_legacy_code = obj.get(CSVHeadersV2.code)  # CSV uses same code field for both
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
                        "csv_row": self._row_to_csv_line(sign_data, self.delimiter),
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
                        "csv_row": self._row_to_csv_line(sign_data, self.delimiter),
                    }
                )

        return {"REPORT_TYPE": "INVALID DEVICE TYPE CODES", "results": results}

    def _get_status_internal_status_mismatch_report(self) -> dict[str, Any]:
        """Report mismatches between status field (from CSV) and internal_status (calculated from DB).

        Identifies problematic inconsistencies:
        - status="New" but internal_status="unchanged" or "changed" (claims new but exists in DB)
        - status="Unchanged" but internal_status="new" or "changed" (claims unchanged but doesn't match)
        - status="Changed" but internal_status="new" or "unchanged" (claims changed but doesn't match)
        - status="Removed" but internal_status="new" (claims removed but never existed in DB)

        Returns:
            dict[str, Any]: Report dictionary with REPORT_TYPE and results keys.
                Each result contains object_type, source_id, status, internal_status,
                db_code (from database), csv_code (from CSV), and mismatch reason.
        """
        results = []

        # Define expected internal_status for each status value
        expected_mapping = {
            "New": {"new"},
            "Unchanged": {"unchanged"},
            "Changed": {"changed"},
            "Removed": {"unchanged", "changed"}  # Removed items should exist in DB (unchanged or changed)
        }

        # Check traffic signs
        for source_id, sign_data in self.signs_by_id.items():
            status = sign_data.get(CSVHeadersV2.status, "").strip()
            internal_status = sign_data.get("internal_status", "").strip()
            csv_code = sign_data.get(CSVHeadersV2.code, "").strip()
            db_code = self.sign_reals_by_source_id.get(source_id)

            # Normalize status for case-insensitive comparison
            status_normalized = status.capitalize() if status else ""

            if status_normalized in expected_mapping:
                expected_internal_statuses = expected_mapping[status_normalized]
                if internal_status not in expected_internal_statuses:
                    # Determine mismatch reason
                    if status_normalized == "New" and internal_status in ["unchanged", "changed"]:
                        reason = "Marked as New but already exists in database"
                    elif status_normalized == "Unchanged" and internal_status == "new":
                        reason = "Marked as Unchanged but not found in database"
                    elif status_normalized == "Unchanged" and internal_status == "changed":
                        reason = "Marked as Unchanged but device type code differs from database"
                    elif status_normalized == "Changed" and internal_status == "new":
                        reason = "Marked as Changed but not found in database"
                    elif status_normalized == "Changed" and internal_status == "unchanged":
                        reason = "Marked as Changed but device type code matches database"
                    elif status_normalized == "Removed" and internal_status == "new":
                        reason = "Marked as Removed but not found in database"
                    else:
                        reason = f"Status '{status}' incompatible with internal_status '{internal_status}'"

                    results.append({
                        "object_type": "traffic_sign",
                        "source_id": source_id,
                        "status": status,
                        "internal_status": internal_status,
                        "db_code": db_code,
                        "csv_code": csv_code,
                        "mismatch_reason": reason,
                    })

        # Check additional signs
        for source_id, sign_data in self.additional_signs_by_id.items():
            status = sign_data.get(CSVHeadersV2.status, "").strip()
            internal_status = sign_data.get("internal_status", "").strip()
            csv_code = sign_data.get(CSVHeadersV2.code, "").strip()
            db_code = self.additional_sign_reals_by_source_id.get(source_id)

            # Normalize status for case-insensitive comparison
            status_normalized = status.capitalize() if status else ""

            if status_normalized in expected_mapping:
                expected_internal_statuses = expected_mapping[status_normalized]
                if internal_status not in expected_internal_statuses:
                    # Determine mismatch reason
                    if status_normalized == "New" and internal_status in ["unchanged", "changed"]:
                        reason = "Marked as New but already exists in database"
                    elif status_normalized == "Unchanged" and internal_status == "new":
                        reason = "Marked as Unchanged but not found in database"
                    elif status_normalized == "Unchanged" and internal_status == "changed":
                        reason = "Marked as Unchanged but device type code differs from database"
                    elif status_normalized == "Changed" and internal_status == "new":
                        reason = "Marked as Changed but not found in database"
                    elif status_normalized == "Changed" and internal_status == "unchanged":
                        reason = "Marked as Changed but device type code matches database"
                    elif status_normalized == "Removed" and internal_status == "new":
                        reason = "Marked as Removed but not found in database"
                    else:
                        reason = f"Status '{status}' incompatible with internal_status '{internal_status}'"

                    results.append({
                        "object_type": "additional_sign",
                        "source_id": source_id,
                        "status": status,
                        "internal_status": internal_status,
                        "db_code": db_code,
                        "csv_code": csv_code,
                        "mismatch_reason": reason,
                    })

        return {"REPORT_TYPE": "STATUS AND INTERNAL_STATUS MISMATCH", "results": results}

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
                            "found_in_previous_csv": source_id in self.old_mount_source_ids,
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
                            "found_in_previous_csv": source_id in self.old_sign_source_ids,
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
                            "found_in_previous_csv": source_id in self.old_sign_source_ids,
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
