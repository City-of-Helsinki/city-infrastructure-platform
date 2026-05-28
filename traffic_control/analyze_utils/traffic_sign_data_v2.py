"""TrafficSignAnalyzerV2 entry point.
Implementation is split across focused mixin modules:
- traffic_sign_data_v2_constants.py    constants and CSVHeadersV2
- traffic_sign_data_v2_code_transform.py  CodeTransformMixin
- traffic_sign_data_v2_db_builders.py  DbBuilderMixin
- traffic_sign_data_v2_data_loading.py DataLoadingMixin
- traffic_sign_data_v2_reports.py      ReportsMixin
- traffic_sign_data_v2_status_reports.py StatusReportsMixin
"""
from .traffic_sign_data_v2_code_transform import CodeTransformMixin
from .traffic_sign_data_v2_data_loading import DataLoadingMixin
from .traffic_sign_data_v2_db_builders import DbBuilderMixin
from .traffic_sign_data_v2_reports import ReportsMixin
from .traffic_sign_data_v2_status_reports import StatusReportsMixin


class TrafficSignAnalyzerV2(
    CodeTransformMixin,
    DbBuilderMixin,
    DataLoadingMixin,
    ReportsMixin,
    StatusReportsMixin,
):
    """Analyzer for new traffic sign CSV format with status field."""

    def __init__(
        self,
        mount_file: str,
        sign_file: str,
        previous_mount_file: str | None = None,
        previous_sign_file: str | None = None,
        delimiter: str = ",",
        output_dir: str | None = None,
    ) -> None:
        """Initialize TrafficSignAnalyzerV2 with CSV files.
        Args:
            mount_file (str): Path to the mount CSV file.
            sign_file (str): Path to the sign CSV file.
            previous_mount_file (str | None): Path to the previous mount CSV file. Defaults to None.
            previous_sign_file (str | None): Path to the previous sign CSV file. Defaults to None.
            delimiter (str): CSV delimiter character. Defaults to ",".
            output_dir (str | None): Directory for output CSV. If None, uses input file's directory. Defaults to None.
        """
        self.delimiter = delimiter
        self.mount_rows = self._read_csv_file(mount_file, delimiter)
        self.sign_rows = self._read_csv_file(sign_file, delimiter)
        self.previous_mount_rows = self._read_csv_file(previous_mount_file, ";") if previous_mount_file else []
        self.previous_sign_rows = self._read_csv_file(previous_sign_file, ";") if previous_sign_file else []
        self.old_mount_source_ids = self._build_source_id_set(self.previous_mount_rows)
        self.old_sign_source_ids = self._build_source_id_set(self.previous_sign_rows)
        self.filtered_signs: list = []
        self.enriched_signs: list = []
        self.code_replacements: list = []
        self.code_replacement_failures: list = []
        self._add_internal_additional_info_to_rows(self.sign_rows)
        self.sign_rows = self._filter_and_enrich_sign_rows(self.sign_rows)
        self.sign_reals_by_source_id = self._build_sign_reals_by_source_id()
        self.additional_sign_reals_by_source_id = self._build_additional_sign_reals_by_source_id()
        self.signpost_reals_by_source_id = self._build_signpost_reals_by_source_id()
        self._add_internal_status_to_rows(self.sign_rows)
        self._save_processed_csv(sign_file, self.sign_rows, delimiter, output_dir)
        self.code_to_device_type_id = self._build_code_to_device_type_mapping()
        self.mounts_by_id = self._get_objects_by_id(self.mount_rows)
        self.all_signs_by_id = self._get_objects_by_id(self.sign_rows)
        self.signs_by_id = self._get_signs_by_id(self.sign_rows)
        self.signs_by_mount_id = self._get_signs_by_mount_id()
        self.additional_signs_by_id = self._get_additional_signs_by_id(self.sign_rows)
        self.additional_signs_by_mount_id = self._get_additional_signs_by_mount_id()
        self.signposts_by_id = self._get_signposts_by_id(self.sign_rows)
        self.signposts_by_mount_id = self._get_signposts_by_mount_id()
        self._combine_mounts_with_signs(self.mounts_by_id, self.additional_signs_by_mount_id, self.signs_by_mount_id)
        self.no_mounts_per_sign_id = self._get_non_existing_mounts_by_sign_id()
        self.no_mounts_per_additional_sign_id = self._get_non_existing_mounts_by_additional_sign_id()
        self.no_mounts_per_signpost_id = self._get_non_existing_mounts_by_signpost_id()
        self.mounts_by_status = self._segregate_by_status(self.mounts_by_id.values())
        self.signs_by_status = self._segregate_by_status(self.signs_by_id.values())
        self.additional_signs_by_status = self._segregate_by_status(self.additional_signs_by_id.values())
        self.signposts_by_status = self._segregate_by_status(self.signposts_by_id.values())
        self.mount_reals_by_source_id_set = self._build_mount_reals_by_source_id()
        self.sign_reals_legacy_codes_by_source_id = self._build_sign_reals_legacy_codes_by_source_id()
        self.additional_sign_reals_legacy_codes_by_source_id = (
            self._build_additional_sign_reals_legacy_codes_by_source_id()
        )
        self.signpost_reals_legacy_codes_by_source_id = self._build_signpost_reals_legacy_codes_by_source_id()
        self.mount_source_id_to_db_id = self._build_mount_source_id_to_db_id()
        self.sign_source_id_to_db_id = self._build_sign_source_id_to_db_id()
        self.additional_sign_source_id_to_db_id = self._build_additional_sign_source_id_to_db_id()
        self.signpost_source_id_to_db_id = self._build_signpost_source_id_to_db_id()
        self.mount_source_id_to_db_location = self._build_mount_source_id_to_db_location()
        self.sign_source_id_to_db_location = self._build_sign_source_id_to_db_location()
        self.additional_sign_source_id_to_db_location = self._build_additional_sign_source_id_to_db_location()
        self.signpost_source_id_to_db_location = self._build_signpost_source_id_to_db_location()

    def analyze(self) -> list[dict]:
        """Generate all analysis reports.

        Returns:
            list[dict]: List of report dictionaries, each with REPORT_TYPE and results keys.
        """
        return [
            # CSV preprocessing
            self._get_filtered_signs_report(),
            self._get_enriched_signs_report(),
            self._get_code_replacements_report(),
            self._get_code_replacement_failures_report(),
            # Status distribution
            self._get_status_distribution_report(),
            self._get_invalid_status_report(),
            # Status records
            self._get_new_records_report(),
            self._get_change_records_report(),
            self._get_unchanged_records_report(),
            self._get_remove_records_report(),
            self._get_remove_with_invalid_location_report(),
            # Non-existing mount references
            self._get_non_existing_mounts_for_additional_signs(),
            self._get_non_existing_mounts_for_signposts(),
            self._get_non_existing_mounts_for_signs(),
            # Mountless signs
            self._get_mountless_additional_signs(),
            self._get_mountless_signposts(),
            self._get_mountless_signs(),
            # Sign relationships
            self._get_signless_additional_signs(),
            self._get_main_signs_with_parent_report(),
            self._get_removed_parents_referenced_by_active_additional_signs(),
            self._get_signposts_that_are_both_parent_and_child_report(),
            # Distance reports
            self._get_mount_distances(),
            self._get_additional_sign_distances(),
            self._get_sign_distances(),
            # Duplicate detection
            self._get_duplicate_signs_on_same_mount_by_device_type(),
            self._get_duplicate_signs_on_same_mount_exact_code(),
            self._get_added_double_sided_zebra_crossings(),
            # Mount health
            self._get_mounts_without_any_signs_report(),
            self._get_mounts_with_removed_signs_report(),
            # Validation
            self._get_timestamp_format_validation_report(),
            self._get_invalid_device_type_codes_report(),
            self._get_status_internal_status_mismatch_report(),
            # Missing from database
            self._get_missing_mounts_from_database_report(),
            self._get_missing_traffic_signs_from_database_report(),
            self._get_missing_additional_signs_from_database_report(),
            self._get_missing_signposts_from_database_report(),
            # Found in database
            self._get_mounts_found_in_database_report(),
            self._get_traffic_signs_found_in_database_report(),
            self._get_additional_signs_found_in_database_report(),
            self._get_signposts_found_in_database_report(),
            # CSV to DB location distances
            self._get_mount_csv_to_db_location_distance_report(),
            self._get_traffic_sign_csv_to_db_location_distance_report(),
            self._get_additional_sign_csv_to_db_location_distance_report(),
            self._get_signpost_csv_to_db_location_distance_report(),
        ]
