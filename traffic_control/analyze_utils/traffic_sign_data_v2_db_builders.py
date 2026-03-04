"""Database lookup builder mixin and CSV utility statics for TrafficSignAnalyzerV2."""
import csv
import os
from datetime import datetime
from typing import Any, Type

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignImporter
from traffic_control.models.additional_sign import AdditionalSignReal
from traffic_control.models.common import TrafficControlDeviceType
from traffic_control.models.mount import MountReal
from traffic_control.models.signpost import SignpostReal
from traffic_control.models.traffic_sign import TrafficSignReal

from .traffic_sign_data_v2_constants import CSVHeadersV2


class DbBuilderMixin:
    """Mixin providing CSV I/O utilities and database lookup builder methods."""

    @staticmethod
    def _read_csv_file(csv_file_path: str, delimiter: str) -> list[dict]:
        """Read CSV file into memory with specified delimiter.

        Args:
            csv_file_path (str): Path to the CSV file.
            delimiter (str): CSV delimiter character to use.

        Returns:
            list[dict]: List of dictionaries representing CSV rows.
        """
        with open(csv_file_path) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return [{k: row[k].strip() for k in row} for row in reader]

    @staticmethod
    def _build_source_id_set(csv_rows: list[dict]) -> set[str]:
        """Build set of source IDs from CSV rows.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.

        Returns:
            set[str]: Set of source ID strings from the rows.
        """
        return {row.get(CSVHeadersV2.id, "") for row in csv_rows if row.get(CSVHeadersV2.id, "")}

    @staticmethod
    def _save_processed_csv(
        original_file_path: str, processed_rows: list[dict], delimiter: str, output_dir: str | None = None
    ) -> None:
        """Save processed and enriched sign data to CSV file.

        Creates a new CSV file in the same directory as the original file with
        suffix '_filtered_<timestamp>' added to the filename.

        Args:
            original_file_path (str): Path to the original CSV file.
            processed_rows (list[dict]): Processed and enriched sign rows to save.
            delimiter (str): CSV delimiter character to use.
            output_dir (str | None): Directory to write the output file to. If None, uses original file's directory.
        """
        if not processed_rows:
            print("All entries have been filtered out. No CSV saved")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = output_dir if output_dir else os.path.dirname(original_file_path)
        basename = os.path.basename(original_file_path)
        name_without_ext, ext = os.path.splitext(basename)
        output_filename = f"{name_without_ext}_processed_{timestamp}{ext}"
        output_path = os.path.join(directory, output_filename)
        fieldnames = list(processed_rows[0].keys())
        with open(output_path, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(processed_rows)
        print(f"Processed CSV saved to: {output_path}")

    @staticmethod
    def _row_to_csv_line(row: dict, delimiter: str) -> str:
        """Convert a CSV row dictionary back to a CSV line string.

        Args:
            row (dict): Dictionary representing a CSV row.
            delimiter (str): CSV delimiter character to use.

        Returns:
            str: CSV line string with values joined by delimiter.
        """
        import io

        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerow(row.values())
        return output.getvalue().strip()

    @staticmethod
    def _build_code_to_device_type_mapping() -> dict[str, Any]:
        """Build mapping from both code and legacy_code to device type ID.

        Returns:
            dict[str, Any]: Dictionary mapping device codes to device type IDs.
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
    def _build_device_type_attr_map(model_class: Type, attr: str) -> dict[str, str | None]:
        """Build mapping from source_id to a device_type attribute for active objects.

        Args:
            model_class (type): Django model class.
            attr (str): Attribute name on device_type to extract.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to the device_type attribute value.
        """
        return {
            obj.source_id: getattr(obj.device_type, attr)
            for obj in model_class.objects.filter(
                source_name__startswith=TrafficSignImporter.SOURCE_NAME,
                is_active=True,
            ).select_related("device_type")
        }

    @staticmethod
    def _build_sign_reals_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.code for active TrafficSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type code.
        """
        return DbBuilderMixin._build_device_type_attr_map(TrafficSignReal, "code")

    @staticmethod
    def _build_additional_sign_reals_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.code for active AdditionalSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type code.
        """
        return DbBuilderMixin._build_device_type_attr_map(AdditionalSignReal, "code")

    @staticmethod
    def _build_signpost_reals_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.code for active SignpostReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type code.
        """
        return DbBuilderMixin._build_device_type_attr_map(SignpostReal, "code")

    @staticmethod
    def _build_sign_reals_legacy_codes_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.legacy_code for TrafficSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type legacy_code.
        """
        return DbBuilderMixin._build_device_type_attr_map(TrafficSignReal, "legacy_code")

    @staticmethod
    def _build_additional_sign_reals_legacy_codes_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.legacy_code for AdditionalSignReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type legacy_code.
        """
        return DbBuilderMixin._build_device_type_attr_map(AdditionalSignReal, "legacy_code")

    @staticmethod
    def _build_signpost_reals_legacy_codes_by_source_id() -> dict[str, str | None]:
        """Build mapping from source_id to device_type.legacy_code for SignpostReal objects.

        Returns:
            dict[str, str | None]: Dictionary mapping source_id to device_type legacy_code.
        """
        return DbBuilderMixin._build_device_type_attr_map(SignpostReal, "legacy_code")

    @staticmethod
    def _build_source_id_to_db_id(model_class: Type) -> dict[str, str]:
        """Build mapping from source_id to db_id for objects of the given model.

        Args:
            model_class (type): Django model class.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return {
            obj.source_id: obj.id
            for obj in model_class.objects.filter(source_name__startswith=TrafficSignImporter.SOURCE_NAME)
        }

    @staticmethod
    def _build_mount_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for MountReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return DbBuilderMixin._build_source_id_to_db_id(MountReal)

    @staticmethod
    def _build_sign_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for TrafficSignReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return DbBuilderMixin._build_source_id_to_db_id(TrafficSignReal)

    @staticmethod
    def _build_additional_sign_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for AdditionalSignReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return DbBuilderMixin._build_source_id_to_db_id(AdditionalSignReal)

    @staticmethod
    def _build_signpost_source_id_to_db_id() -> dict[str, str]:
        """Build mapping from source_id to db_id for SignpostReal objects.

        Returns:
            dict[str, str]: Dictionary mapping source_id to db_id.
        """
        return DbBuilderMixin._build_source_id_to_db_id(SignpostReal)

    @staticmethod
    def _build_source_id_to_db_location(
        model_class: Type,
        include_device_type_code: bool = False,
        include_mount_type: bool = False,
    ) -> dict[str, tuple]:
        """Build mapping from source_id to a location tuple for the given model.

        Tuple layout: (db_id, location, attachment_url, db_code, db_mount_type)
        Unused slots are set to None.

        Args:
            model_class (type): Django model class.
            include_device_type_code (bool): Whether to fetch and include device_type.code. Defaults to False.
            include_mount_type (bool): Whether to fetch and include mount_type. Defaults to False.

        Returns:
            dict[str, tuple]: Dictionary mapping source_id to
                (db_id, Point, attachment_url, db_code, db_mount_type) tuples.
        """
        qs = model_class.objects.filter(
            source_name__startswith=TrafficSignImporter.SOURCE_NAME,
        )
        if include_device_type_code:
            return {
                obj.source_id: (
                    obj.id,
                    obj.location,
                    obj.attachment_url,
                    obj.device_type.code if obj.device_type else None,
                    None,
                )
                for obj in qs.select_related("device_type").only(
                    "source_id", "id", "location", "attachment_url", "device_type__code", "device_type__id"
                )
            }
        if include_mount_type:
            return {
                obj.source_id: (
                    obj.id,
                    obj.location,
                    obj.attachment_url,
                    None,
                    obj.mount_type.code if obj.mount_type else None,
                )
                for obj in qs.select_related("mount_type").only(
                    "source_id", "id", "location", "attachment_url", "mount_type__code", "mount_type__id"
                )
            }
        return {
            obj.source_id: (obj.id, obj.location, obj.attachment_url, None, None)
            for obj in qs.only("source_id", "id", "location", "attachment_url")
        }

    @staticmethod
    def _build_mount_source_id_to_db_location() -> dict[str, tuple]:
        """Build location mapping for MountReal objects including mount_type.

        Returns:
            dict[str, tuple]: Dictionary mapping source_id to
                (db_id, Point, attachment_url, None, db_mount_type) tuples.
        """
        return DbBuilderMixin._build_source_id_to_db_location(MountReal, include_mount_type=True)

    @staticmethod
    def _build_sign_source_id_to_db_location() -> dict[str, tuple]:
        """Build location mapping for TrafficSignReal objects including device_type code.

        Returns:
            dict[str, tuple]: Dictionary mapping source_id to (db_id, Point, attachment_url, db_code, None) tuples.
        """
        return DbBuilderMixin._build_source_id_to_db_location(TrafficSignReal, include_device_type_code=True)

    @staticmethod
    def _build_additional_sign_source_id_to_db_location() -> dict[str, tuple]:
        """Build location mapping for AdditionalSignReal objects including device_type code.

        Returns:
            dict[str, tuple]: Dictionary mapping source_id to (db_id, Point, attachment_url, db_code, None) tuples.
        """
        return DbBuilderMixin._build_source_id_to_db_location(AdditionalSignReal, include_device_type_code=True)

    @staticmethod
    def _build_signpost_source_id_to_db_location() -> dict[str, tuple]:
        """Build location mapping for SignpostReal objects including device_type code.

        Returns:
            dict[str, tuple]: Dictionary mapping source_id to (db_id, Point, attachment_url, db_code, None) tuples.
        """
        return DbBuilderMixin._build_source_id_to_db_location(SignpostReal, include_device_type_code=True)
