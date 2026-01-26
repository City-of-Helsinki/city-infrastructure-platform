import csv
import os
from typing import Dict, List, Set

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction

from traffic_control.geometry_utils import geometry_is_legit, get_3d_geometry
from traffic_control.models.plan import Plan


class PlanGeometryImporter:
    """Imports plan geometries from CSV file containing WKT MultiPolygon data.

    Validates geometries and matches plans by diary_number, then updates
    location and derive_location fields.
    """

    def __init__(self, csv_file_path: str) -> None:
        """Initialize the importer with a CSV file path.

        Args:
            csv_file_path (str): Path to the CSV file containing plan geometries.
        """
        self.csv_file_path = csv_file_path
        self.results: List[Dict] = []
        self._seen_diary_numbers: Set[str] = set()

    def parse_csv(self) -> None:
        """Parse CSV file and build intermediate data structure with validation.

        Reads semicolon-delimited CSV file and validates each row for:
        - Missing diary numbers
        - Duplicate diary numbers within CSV
        - Empty geometries
        - Invalid WKT format

        Results are stored in self.results with appropriate result_type and error_message.
        """
        with open(self.csv_file_path, mode="r", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=";")

            for row_number, row in enumerate(reader, start=1):
                result = {
                    "row_number": row_number,
                    "diaari": row.get("diaari", "").strip(),
                    "fid": row.get("fid", ""),
                    "piirustusnumero": row.get("piirustusnumero", ""),
                    "decision_id": row.get("decision_id", ""),
                    "result_type": None,
                    "error_message": None,
                    "plan_id": None,
                    "geometry": None,
                }

                # Check for missing diary number
                if not result["diaari"]:
                    result["result_type"] = "missing_diary_number"
                    result["error_message"] = "Missing diary number in CSV"
                    self.results.append(result)
                    continue

                # Check for duplicate diary number in CSV
                if result["diaari"] in self._seen_diary_numbers:
                    result["result_type"] = "duplicate_diary_number"
                    result["error_message"] = f"Duplicate diary number: {result['diaari']}"
                    self.results.append(result)
                    continue

                self._seen_diary_numbers.add(result["diaari"])

                # Get WKT geometry
                wkt_geom = row.get("wkt_geom", "").strip()
                result["wkt_geom"] = wkt_geom

                # Check for empty geometry
                if "EMPTY" in wkt_geom.upper():
                    result["result_type"] = "empty_geometry"
                    result["error_message"] = "Geometry is EMPTY"
                    self.results.append(result)
                    continue

                # Parse WKT to geometry object
                try:
                    geometry = GEOSGeometry(wkt_geom, srid=settings.SRID)
                    result["geometry"] = geometry
                except Exception as e:
                    result["result_type"] = "invalid_wkt"
                    result["error_message"] = f"Invalid WKT: {str(e)}"
                    self.results.append(result)
                    continue

                # Store for further processing
                self.results.append(result)

    def _set_geometry_error(self, result: Dict, error_type: str, error_message: str) -> None:
        """Set geometry validation error in result.

        Args:
            result (Dict): Result dictionary to update.
            error_type (str): Type of geometry error.
            error_message (str): Error message description.
        """
        result["result_type"] = error_type
        result["error_message"] = error_message

    def _validate_geometry(self, result: Dict) -> bool:
        """Validate geometry type, emptiness, 3D conversion, topology, and bounds.

        Args:
            result (Dict): Result dictionary containing geometry to validate.

        Returns:
            bool: True if validation passed, False if error was set.
        """
        geometry = result["geometry"]

        # Check geometry type and emptiness
        if geometry.geom_type != "MultiPolygon":
            self._set_geometry_error(
                result, "invalid_geometry_type", f"Expected MultiPolygon, got {geometry.geom_type}"
            )
            return False

        if geometry.empty:
            self._set_geometry_error(result, "empty_geometry", "Geometry is empty")
            return False

        # Convert to 3D geometry and validate topology/bounds
        try:
            geometry_3d = get_3d_geometry(geometry, 0.0)
            result["geometry"] = geometry_3d

            if not geometry_3d.valid:
                self._set_geometry_error(
                    result, "invalid_geometry_topology", f"Geometry has topology errors: {geometry_3d.valid_reason}"
                )
                return False

            if not geometry_is_legit(geometry_3d):
                self._set_geometry_error(
                    result, "invalid_geometry_bounds", "Geometry is outside valid projection boundaries"
                )
                return False

        except Exception as e:
            self._set_geometry_error(result, "invalid_geometry_type", f"Failed to convert to 3D: {str(e)}")
            return False

        return True

    def _has_exact_match(self, csv_dn: str, plan_drawing_numbers: List[str]) -> bool:
        """Check if CSV drawing number has exact match in plan drawing numbers.

        Args:
            csv_dn (str): CSV drawing number to check.
            plan_drawing_numbers (List[str]): Plan's drawing numbers.

        Returns:
            bool: True if exact match exists.
        """
        return csv_dn in plan_drawing_numbers

    def _has_partial_match(self, csv_dn: str, plan_drawing_numbers: List[str]) -> bool:
        """Check if CSV drawing number has partial match (first 4 chars) in plan drawing numbers.

        Args:
            csv_dn (str): CSV drawing number to check.
            plan_drawing_numbers (List[str]): Plan's drawing numbers.

        Returns:
            bool: True if partial match exists.
        """
        if len(csv_dn) < 4:
            return False
        prefix = csv_dn[:4]
        return any(dn.startswith(prefix) for dn in plan_drawing_numbers)

    def _check_any_match(self, csv_drawing_numbers: List[str], plan_drawing_numbers: List[str]) -> bool:
        """Check if any CSV drawing number matches (exact or partial) plan drawing numbers.

        Args:
            csv_drawing_numbers (List[str]): Drawing numbers from CSV.
            plan_drawing_numbers (List[str]): Plan's drawing numbers.

        Returns:
            bool: True if at least one match found.
        """
        for csv_dn in csv_drawing_numbers:
            if self._has_exact_match(csv_dn, plan_drawing_numbers):
                return True
            if self._has_partial_match(csv_dn, plan_drawing_numbers):
                return True
        return False

    def _validate_drawing_number(self, result: Dict, plan: Plan) -> bool:
        """Validate drawing number match and set merge_drawing_numbers flag.

        Args:
            result (Dict): Result dictionary to update.
            plan (Plan): Plan object to validate against.

        Returns:
            bool: True if validation passed, False if error was set.
        """
        csv_drawing_numbers_str = str(result["piirustusnumero"]).strip()
        csv_drawing_numbers = []
        should_merge_drawing_numbers = False

        if csv_drawing_numbers_str and csv_drawing_numbers_str != "0":
            csv_drawing_numbers = [dn.strip() for dn in csv_drawing_numbers_str.split(",") if dn.strip()]
            has_match = self._check_any_match(csv_drawing_numbers, plan.drawing_numbers)

            if has_match or len(plan.drawing_numbers) == 0:
                should_merge_drawing_numbers = True
            else:
                result["result_type"] = "drawing_number_mismatch"
                result["error_message"] = (
                    f"CSV piirustusnumero '{csv_drawing_numbers_str}' not found in "
                    f"Plan drawing_numbers {plan.drawing_numbers}"
                )
                return False

        result["should_merge_drawing_numbers"] = should_merge_drawing_numbers
        result["csv_drawing_numbers"] = csv_drawing_numbers
        return True

    def validate_and_process_rows(self) -> None:
        """Validate geometries and match with Plan records.

        For each row in self.results, performs:
        - Geometry type validation (must be MultiPolygon)
        - Empty geometry detection
        - 3D geometry conversion
        - Projection boundary validation
        - Plan matching by diary_number
        - Decision ID validation
        - Drawing number validation

        Updates each result dict with appropriate result_type and error_message.
        """
        for result in self.results:
            if result["result_type"] is not None:
                continue

            # Validate geometry
            if not self._validate_geometry(result):
                continue

            # Find matching Plan and validate
            try:
                plan = Plan.objects.filter(is_active=True, diary_number=result["diaari"]).first()

                if not plan:
                    result["result_type"] = "plan_not_found"
                    result["error_message"] = f"No active Plan found with diary_number: {result['diaari']}"
                    continue

                result["plan_id"] = str(plan.id)

                # Validate decision_id match
                if result["decision_id"] and plan.decision_id != result["decision_id"]:
                    result["result_type"] = "decision_id_mismatch"
                    result["error_message"] = (
                        f"CSV decision_id '{result['decision_id']}' does not match "
                        f"Plan decision_id '{plan.decision_id}'"
                    )
                    continue

                # Validate drawing number
                if not self._validate_drawing_number(result, plan):
                    continue

                result["result_type"] = "success"

            except Exception as e:
                result["result_type"] = "plan_not_found"
                result["error_message"] = f"Error querying Plan: {str(e)}"

    def _merge_drawing_numbers(self, plan_drawing_numbers: List[str], csv_drawing_numbers: List[str]) -> List[str]:
        """Merge CSV drawing numbers with existing plan drawing numbers.

        Partial matches are replaced by CSV values. For example:
        - CSV has "1234", DB has "1234-4" → Result: "1234" (replaces "1234-4")
        - CSV has "1234", DB has "6789" → Result: "1234", "6789" (both preserved)

        Args:
            plan_drawing_numbers (List[str]): Existing drawing numbers from plan.
            csv_drawing_numbers (List[str]): Drawing numbers from CSV to merge.

        Returns:
            List[str]: Merged and sorted list of drawing numbers.
        """
        new_drawing_numbers = []
        replaced_prefixes = set()

        # Identify prefixes that will be replaced
        for csv_dn in csv_drawing_numbers:
            if len(csv_dn) >= 4:
                replaced_prefixes.add(csv_dn[:4])

        # Add existing drawing numbers, skip those that match replaced prefixes
        for existing_dn in plan_drawing_numbers:
            should_skip = False
            for prefix in replaced_prefixes:
                if existing_dn.startswith(prefix) and existing_dn not in csv_drawing_numbers:
                    should_skip = True
                    break
            if not should_skip:
                new_drawing_numbers.append(existing_dn)

        # Add all CSV drawing numbers
        for csv_dn in csv_drawing_numbers:
            if csv_dn not in new_drawing_numbers:
                new_drawing_numbers.append(csv_dn)

        return sorted(new_drawing_numbers)

    def _check_geometry_match(self, plan_location, csv_geometry) -> bool:
        """Check if plan location matches CSV geometry.

        Args:
            plan_location: Plan's current location geometry.
            csv_geometry: Geometry from CSV.

        Returns:
            bool: True if geometries match, False otherwise.
        """
        if not plan_location or not csv_geometry:
            return False

        try:
            return plan_location.equals(csv_geometry)
        except Exception:
            # GEOS comparison can fail for invalid geometries
            return False

    def _build_update_fields(self, plan: Plan, result: Dict) -> tuple:
        """Build update fields and track changes for a plan.

        Args:
            plan (Plan): Plan object to update.
            result (Dict): Result dictionary with update information.

        Returns:
            tuple: (update_fields dict, fields_changed list)
        """
        fields_changed = []
        update_fields = {}

        # Check if location geometries match
        geometries_match = self._check_geometry_match(plan.location, result["geometry"])

        # Location field (only update if different)
        if not geometries_match:
            old_location = "None" if not plan.location else plan.location.ewkt
            new_location = result["geometry"].ewkt
            update_fields["location"] = result["geometry"]
            fields_changed.append({"field": "location", "old_value": old_location, "new_value": new_location})

        # derive_location field (always set to False if not already)
        if plan.derive_location is not False:
            update_fields["derive_location"] = False
            fields_changed.append(
                {
                    "field": "derive_location",
                    "old_value": str(plan.derive_location),
                    "new_value": "False",
                }
            )

        # Merge drawing numbers if needed
        if result.get("should_merge_drawing_numbers", False):
            old_drawing_numbers = list(plan.drawing_numbers)
            csv_drawing_numbers = result.get("csv_drawing_numbers", [])
            new_drawing_numbers = self._merge_drawing_numbers(old_drawing_numbers, csv_drawing_numbers)

            if set(new_drawing_numbers) != set(old_drawing_numbers):
                update_fields["drawing_numbers"] = new_drawing_numbers
                fields_changed.append(
                    {
                        "field": "drawing_numbers",
                        "old_value": str(old_drawing_numbers),
                        "new_value": str(new_drawing_numbers),
                    }
                )

        return update_fields, fields_changed

    def _process_plan_update(self, result: Dict) -> bool:
        """Process a single plan update.

        Args:
            result (Dict): Result dictionary with plan update information.

        Returns:
            bool: True if plan was updated, False if skipped.
        """
        plan = Plan.objects.get(pk=result["plan_id"])
        update_fields, fields_changed = self._build_update_fields(plan, result)

        if update_fields:
            result["update_details"] = {
                "csv_row": result["row_number"],
                "plan_id": result["plan_id"],
                "diary_number": result["diaari"],
                "fields_changed": fields_changed,
            }
            Plan.objects.filter(pk=result["plan_id"]).update(**update_fields)
            return True

        # No changes needed, mark as skipped
        result["result_type"] = "skipped_no_changes"
        result["error_message"] = "Location geometry matches existing Plan, no update needed"
        result["update_details"] = {
            "csv_row": result["row_number"],
            "plan_id": result["plan_id"],
            "diary_number": result["diaari"],
            "fields_changed": [],
        }
        return False

    def _get_success_results(self) -> List[Dict]:
        """Get list of results marked as success.

        Returns:
            List[Dict]: Filtered list of successful results.
        """
        return [r for r in self.results if r["result_type"] == "success"]

    def _update_plans_in_transaction(self) -> int:
        """Update plans within a database transaction.

        Returns:
            int: Number of plans successfully updated.
        """
        update_count = 0
        success_results = self._get_success_results()

        with transaction.atomic():
            for result in success_results:
                if self._process_plan_update(result):
                    update_count += 1

        return update_count

    def update_plans(self, dry_run: bool = False) -> Dict[str, int]:
        """Update Plan locations in database within transaction.

        Args:
            dry_run (bool): If True, only count updates without modifying database. Defaults to False.

        Returns:
            Dict[str, int]: Summary statistics with keys:
                - total_rows: Total number of rows processed
                - updated: Number of plans updated (or would be updated in dry-run)
                - errors: Number of rows with errors
        """
        if dry_run:
            update_count = len(self._get_success_results())
        else:
            update_count = self._update_plans_in_transaction()

        return {
            "total_rows": len(self.results),
            "updated": update_count,
            "errors": len(self.results) - update_count,
        }

    def get_results(self) -> List[Dict[str, any]]:
        """Get JSON-serializable results without geometry objects.

        Converts internal result structure to JSON-safe format by excluding
        non-serializable geometry and wkt_geom fields.

        Returns:
            List[Dict[str, any]]: List of result dictionaries containing:
                - row_number: Row number in CSV
                - diaari: Diary number from CSV
                - fid: Feature ID
                - piirustusnumero: Drawing number
                - decision_id: Decision ID
                - result_type: Type of validation result
                - error_message: Error description (if applicable)
                - plan_id: UUID of matched Plan (if successful)
        """
        json_results = []
        for result in self.results:
            json_result = {
                "row_number": result["row_number"],
                "diaari": result["diaari"],
                "fid": result["fid"],
                "piirustusnumero": result["piirustusnumero"],
                "decision_id": result["decision_id"],
                "result_type": result["result_type"],
                "error_message": result["error_message"],
                "plan_id": result["plan_id"],
            }
            # Include update details if available (only for successful updates)
            if "update_details" in result:
                json_result["update_details"] = result["update_details"]
            json_results.append(json_result)
        return json_results

    def generate_csv_reports(self, output_dir: str) -> None:
        """Generate CSV reports grouped by result type.

        Creates an output directory and writes multiple CSV files:
        - all_results.csv: All processed rows
        - plans_updated.csv: Successfully updated rows
        - plans_not_found.csv: Plans not found by diary_number
        - missing_diary_number.csv: Rows with missing diary numbers
        - duplicate_diary_number.csv: Duplicate diary numbers
        - invalid_geometries.csv: Invalid WKT errors
        - invalid_geometry_type.csv: Wrong geometry type
        - invalid_geometry_bounds.csv: Out of bounds geometries
        - empty_geometry.csv: Empty geometries
        - decision_id_mismatch.csv: Decision ID mismatches
        - drawing_number_mismatch.csv: Drawing number mismatches

        Args:
            output_dir (str): Directory path where CSV reports will be created.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate all_results.csv (summary mode)
        if self.results:
            all_results_path = os.path.join(output_dir, "all_results.csv")
            self._write_csv_report(all_results_path, self.results, summary_mode=True)

        # Generate reports by result type
        result_type_files = {
            "success": "plans_updated.csv",
            "skipped_no_changes": "plans_skipped_no_changes.csv",
            "plan_not_found": "plans_not_found.csv",
            "missing_diary_number": "missing_diary_number.csv",
            "duplicate_diary_number": "duplicate_diary_number.csv",
            "invalid_wkt": "invalid_geometries.csv",
            "invalid_geometry_type": "invalid_geometry_type.csv",
            "invalid_geometry_topology": "invalid_geometry_topology.csv",
            "invalid_geometry_bounds": "invalid_geometry_bounds.csv",
            "empty_geometry": "empty_geometry.csv",
            "decision_id_mismatch": "decision_id_mismatch.csv",
            "drawing_number_mismatch": "drawing_number_mismatch.csv",
        }

        for result_type, filename in result_type_files.items():
            filtered_results = [r for r in self.results if r.get("result_type") == result_type]
            if filtered_results:
                # Write summary version (human-readable)
                filepath = os.path.join(output_dir, filename)
                self._write_csv_report(filepath, filtered_results, summary_mode=True)

                # Write detailed version (with full EWKT) for success and skipped
                if result_type in ("success", "skipped_no_changes"):
                    detailed_filename = filename.replace(".csv", "_detailed.csv")
                    detailed_path = os.path.join(output_dir, detailed_filename)
                    self._write_csv_report(detailed_path, filtered_results, summary_mode=False)

    def _format_field_change(self, fc: Dict, summary_mode: bool) -> str:
        """Format a single field change for CSV output.

        Args:
            fc (Dict): Field change dictionary with 'field', 'old_value', 'new_value'.
            summary_mode (bool): If True, use human-readable format; if False, use full values.

        Returns:
            str: Formatted field change string.
        """
        field_name = fc["field"]
        if field_name == "location" and summary_mode:
            old_val = fc["old_value"]
            new_val = fc["new_value"]

            if old_val == "None":
                old_summary = "None"
            else:
                old_summary = f"MultiPolygon ({old_val.count('(((')} polygons)"

            new_summary = f"MultiPolygon ({new_val.count('(((')} polygons)"
            return f"{field_name}: {old_summary} → {new_summary}"
        else:
            return f"{field_name}: {fc['old_value']} → {fc['new_value']}"

    def _write_csv_report(self, filepath: str, results: List[Dict], summary_mode: bool = True) -> None:
        """Write results to CSV file.

        Args:
            filepath (str): Path to the CSV file to write.
            results (List[Dict]): List of result dictionaries to write.
            summary_mode (bool): If True, use human-readable summaries for geometry fields.
                                If False, include full EWKT values.
        """
        if not results:
            return

        # Define base fields to write
        fieldnames = [
            "row_number",
            "diaari",
            "fid",
            "piirustusnumero",
            "decision_id",
            "result_type",
            "error_message",
            "plan_id",
        ]

        # Add fields_changed summary for success results
        if any(r.get("result_type") in ("success", "skipped_no_changes") for r in results):
            fieldnames.append("fields_changed")

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for result in results:
                row_data = {
                    "row_number": result.get("row_number", ""),
                    "diaari": result.get("diaari", ""),
                    "fid": result.get("fid", ""),
                    "piirustusnumero": result.get("piirustusnumero", ""),
                    "decision_id": result.get("decision_id", ""),
                    "result_type": result.get("result_type", ""),
                    "error_message": result.get("error_message", ""),
                    "plan_id": result.get("plan_id", ""),
                }

                # Add fields_changed information
                if "update_details" in result:
                    fields_changed = result["update_details"].get("fields_changed", [])
                    if fields_changed:
                        separator = "; " if summary_mode else " | "
                        changes_list = [self._format_field_change(fc, summary_mode) for fc in fields_changed]
                        row_data["fields_changed"] = separator.join(changes_list)
                    else:
                        row_data["fields_changed"] = "No changes"

                writer.writerow(row_data)
