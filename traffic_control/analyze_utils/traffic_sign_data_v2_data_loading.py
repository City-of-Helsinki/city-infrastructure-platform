"""Data loading and grouping mixin for TrafficSignAnalyzerV2."""
from django.conf import settings
from django.contrib.gis.geos import Point

from .traffic_sign_data_v2_constants import CSVHeadersV2, VALID_STATUS_VALUES


class DataLoadingMixin:
    """Mixin providing CSV data loading, grouping, and sign classification helpers."""

    @staticmethod
    def _point_from_csv_row(csv_row: dict) -> Point | None:
        """Create a Point from CSV row coordinates.

        Args:
            csv_row (dict): CSV row dictionary containing coordinate fields.

        Returns:
            Point | None: A Point object, or None if coordinates are invalid.
        """
        try:
            return Point(float(csv_row[CSVHeadersV2.coord_x]), float(csv_row[CSVHeadersV2.coord_y]), 0.0)
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _georeferenced_point_from_csv_row(csv_row: dict) -> Point:
        """Create a georeferenced 3D Point from CSV row coordinates with SRID.

        Used for EWKT representations and database location comparisons.

        Args:
            csv_row (dict): CSV row dictionary containing coordinate fields.

        Returns:
            Point: A 3D Point object with SRID.

        Raises:
            KeyError: If a required coordinate field is missing from csv_row.
            ValueError: If coordinate values cannot be converted to float.
        """
        return Point(
            float(csv_row[CSVHeadersV2.coord_x]),
            float(csv_row[CSVHeadersV2.coord_y]),
            float(csv_row[CSVHeadersV2.coord_z]),
            srid=settings.SRID,
        )

    @staticmethod
    def _get_objects_by_id(csv_rows: list[dict], filter_f=None) -> dict:
        """Load objects from CSV rows with optional filtering.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.
            filter_f: Optional filter function to apply to rows.

        Returns:
            dict: Dictionary of objects indexed by ID (flat structure, single object per ID).
        """
        objects_by_id = {}
        for row in csv_rows:
            if filter_f is None or filter_f(row):
                objects_by_id[row[CSVHeadersV2.id]] = row
        return objects_by_id

    def _calculate_distance_to_mount(self, data: dict) -> None:
        """Calculate distance from an object to its mount and store in data['distance_to_mount'].

        Args:
            data (dict): CSV row dict for a sign or additional sign (modified in place).
        """
        mount_data = self.mounts_by_id.get(data.get(CSVHeadersV2.mount_id), None)
        if mount_data:
            mount_point = self._point_from_csv_row(mount_data)
            data["distance_to_mount"] = mount_point.distance(self._point_from_csv_row(data))
        else:
            data["distance_to_mount"] = None

    def _get_signs_by_id(self, csv_rows: list[dict]) -> dict:
        """Get traffic signs (not additional signs) with distance calculations.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.

        Returns:
            dict: Dictionary of traffic signs indexed by ID with calculated distances.
        """
        signs = self._get_objects_by_id(
            csv_rows,
            filter_f=lambda x: not self._is_additional_sign(x) and not self._is_signpost(x),
        )
        for data in signs.values():
            self._calculate_distance_to_mount(data)
        return signs

    def _get_signs_by_mount_id(self) -> dict:
        """Group signs by mount ID.

        Returns:
            dict: Dictionary mapping mount IDs to lists of signs.
        """
        return self._group_by_mount_id(self.signs_by_id)

    @staticmethod
    def _group_by_mount_id(signs_dict: dict) -> dict:
        """Group signs by their mount ID.

        Args:
            signs_dict (dict): Mapping of sign_id to sign data dicts.

        Returns:
            dict: Dictionary mapping mount IDs to lists of sign data dicts.
        """
        grouped: dict = {}
        for v in signs_dict.values():
            grouped.setdefault(v[CSVHeadersV2.mount_id], []).append(v)
        return grouped

    def _get_additional_signs_by_id(self, csv_rows: list[dict]) -> dict:
        """Get additional signs with distance calculations.

        Args:
            csv_rows (list[dict]): List of CSV row dictionaries.

        Returns:
            dict: Dictionary of additional signs indexed by ID with calculated distances.
        """
        additional_signs = self._get_objects_by_id(csv_rows, filter_f=self._is_additional_sign)
        for data in additional_signs.values():
            self._calculate_distance_to_mount(data)
            parent_data = self.signs_by_id.get(data.get(CSVHeadersV2.parent_sign_id), None)
            if parent_data:
                parent_point = self._point_from_csv_row(parent_data)
                data["distance_to_parent"] = parent_point.distance(self._point_from_csv_row(data))
                data["parent_is_additional_sign"] = "No"
                data["parent_code"] = parent_data.get(CSVHeadersV2.code)
            else:
                parent_data = self.all_signs_by_id.get(data.get(CSVHeadersV2.parent_sign_id), None)
                if parent_data:
                    parent_point = self._point_from_csv_row(parent_data)
                    data["distance_to_parent"] = parent_point.distance(self._point_from_csv_row(data))
                    data["parent_is_additional_sign"] = "Yes"
                    data["parent_code"] = parent_data.get(CSVHeadersV2.code)
                else:
                    data["distance_to_parent"] = None
                    data["parent_is_additional_sign"] = None
                    data["parent_code"] = None
        return additional_signs

    def _get_additional_signs_by_mount_id(self):
        """Group additional signs by mount ID."""
        return self._group_by_mount_id(self.additional_signs_by_id)

    def _get_signposts_by_id(self, csv_rows: list[dict]) -> dict:
        """Get signpost signs with distance calculations.

        Args:
            csv_rows (list[dict): List of CSV row dictionaries.

        Returns:
            dict: Dictionary of signposts indexed by ID with calculated distances.
        """
        signposts = self._get_objects_by_id(csv_rows, filter_f=self._is_signpost)
        for data in signposts.values():
            self._calculate_distance_to_mount(data)
        return signposts

    def _get_signposts_by_mount_id(self) -> dict:
        """Group signposts by mount ID.

        Returns:
            dict: Dictionary mapping mount IDs to lists of signposts.
        """
        return self._group_by_mount_id(self.signposts_by_id)

    @staticmethod
    def _combine_mounts_with_signs(mounts_by_id, additional_signs_by_mount_id, signs_by_mount_id):
        """Combine mounts with their attached signs."""
        for mount_id, data_d in mounts_by_id.items():
            data_d["additional_signs"] = []
            data_d["signs"] = []
            for entry in additional_signs_by_mount_id.get(mount_id, []):
                data_d["additional_signs"].append(entry)
            for entry in signs_by_mount_id.get(mount_id, []):
                data_d["signs"].append(entry)

    def _get_non_existing_mounts_by_sign_id(self):
        """Find signs with non-existing mount references."""
        return self._get_non_existing_mounts_for(self.signs_by_id)

    def _get_non_existing_mounts_by_additional_sign_id(self):
        """Find additional signs with non-existing mount references."""
        return self._get_non_existing_mounts_for(self.additional_signs_by_id)

    def _get_non_existing_mounts_by_signpost_id(self):
        """Find signposts with non-existing mount references."""
        return self._get_non_existing_mounts_for(self.signposts_by_id)

    def _get_non_existing_mounts_for(self, signs_dict: dict) -> dict:
        """Find signs whose mount_id is not present in the mounts dataset.

        Args:
            signs_dict (dict): Mapping of sign_id to sign data dicts.

        Returns:
            dict: Mapping of sign_id to mount_id for signs with missing mount references.
        """
        return {
            x.get(CSVHeadersV2.id): x.get(CSVHeadersV2.mount_id)
            for x in filter(
                lambda x: x.get(CSVHeadersV2.mount_id) not in self.mounts_by_id.keys(),
                signs_dict.values(),
            )
        }

    @staticmethod
    def _is_additional_sign(row: dict) -> bool:
        """Check if row represents an additional sign."""
        code = row[CSVHeadersV2.code]
        return bool(code and code[0] in ["H", "8"])

    @staticmethod
    def _is_signpost(row: dict) -> bool:
        """Check if row represents a signpost.

        Args:
            row (dict): CSV row dictionary.

        Returns:
            bool: True if the row represents a signpost.
        """
        code = row.get(CSVHeadersV2.code, "")
        if not code:
            return False
        if code in ("6", "7"):
            return False
        return code[0] in ("6", "7", "G", "F")

    @staticmethod
    def _segregate_by_status(objects) -> dict[str, list]:
        """Segregate objects by status field.

        Args:
            objects: Iterable of objects with status field.

        Returns:
            dict[str, list]: Dictionary with status values as keys.
        """
        by_status: dict[str, list] = {
            "New": [],
            "Unchanged": [],
            "Changed": [],
            "Removed": [],
            "invalid": [],
        }
        for obj in objects:
            status = obj.get(CSVHeadersV2.status, "").lower()
            if status in VALID_STATUS_VALUES:
                by_status[status.capitalize()].append(obj)
            else:
                by_status["invalid"].append(obj)
        return by_status
