"""Tests for plan geometry importer functionality."""
import csv

import pytest
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

from traffic_control.analyze_utils.plan_geometry_importer import (
    PlanGeometryImporter,
)
from traffic_control.geometry_utils import get_3d_geometry
from traffic_control.tests.factories import get_user, PlanFactory


@pytest.fixture
def test_user(db):
    """Create a test user.

    Returns:
        User: Test user instance.
    """
    return get_user()


@pytest.fixture
def test_plan(db, test_user):
    """Create a test plan with known diary number.

    Args:
        db: Pytest database fixture.
        test_user: Test user fixture.

    Returns:
        Plan: Test plan instance.
    """
    return PlanFactory(
        diary_number="HEL 2024-12345",
        decision_id="2024-100",
        drawing_numbers=["6593-3", "7000"],
        created_by=test_user,
        updated_by=test_user,
    )


@pytest.fixture
def valid_csv_file(tmp_path):
    """Create a valid CSV file with geometry data.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        str: Path to created CSV file.
    """
    csv_path = tmp_path / "test_geometries.csv"

    # Create simple valid MultiPolygon WKT
    wkt = (
        "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
        "25493859.07 6679719.85, 25493824.78 6679773.23)))"
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
        writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])

    return str(csv_path)


@pytest.fixture
def invalid_geometry_csv(tmp_path):
    """Create CSV file with invalid geometry.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        str: Path to created CSV file.
    """
    csv_path = tmp_path / "invalid_geometries.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
        writer.writerow(["INVALID WKT", "102", "6593", "2024-100", "HEL 2024-12345"])

    return str(csv_path)


@pytest.mark.django_db(transaction=True)
class TestPlanGeometryImporter:
    """Tests for PlanGeometryImporter class."""

    def test_parse_csv_success(self, valid_csv_file):
        """Test successful CSV parsing.

        Args:
            valid_csv_file: Valid CSV file fixture.
        """
        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()

        assert len(importer.results) == 1
        assert importer.results[0]["diaari"] == "HEL 2024-12345"
        assert importer.results[0]["fid"] == "101"
        assert importer.results[0]["piirustusnumero"] == "6593"
        assert importer.results[0]["decision_id"] == "2024-100"
        assert importer.results[0]["geometry"] is not None

    def test_parse_csv_missing_diary_number(self, tmp_path):
        """Test CSV with missing diary number.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "missing_diary.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", ""])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()

        assert len(importer.results) == 1
        assert importer.results[0]["result_type"] == "missing_diary_number"

    def test_parse_csv_duplicate_diary_number(self, tmp_path):
        """Test CSV with duplicate diary numbers.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "duplicate_diary.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])
            writer.writerow([wkt, "102", "6594", "2024-100", "HEL 2024-12345"])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()

        assert len(importer.results) == 2
        duplicate_results = [r for r in importer.results if r["result_type"] == "duplicate_diary_number"]
        assert len(duplicate_results) == 1

    def test_parse_csv_invalid_wkt(self, invalid_geometry_csv):
        """Test CSV with invalid WKT geometry.

        Args:
            invalid_geometry_csv: Invalid geometry CSV fixture.
        """
        importer = PlanGeometryImporter(invalid_geometry_csv)
        importer.parse_csv()

        assert len(importer.results) == 1
        assert importer.results[0]["result_type"] == "invalid_wkt"
        assert "Invalid WKT" in importer.results[0]["error_message"]

    def test_validate_geometry_wrong_type(self, tmp_path):
        """Test validation rejects non-MultiPolygon geometries.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "wrong_type.csv"
        wkt = "POINT (25493824.78 6679773.23)"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert importer.results[0]["result_type"] == "invalid_geometry_type"

    def test_validate_geometry_empty(self, tmp_path):
        """Test validation rejects empty geometries.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "empty_geom.csv"
        wkt = "MULTIPOLYGON EMPTY"

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert importer.results[0]["result_type"] == "empty_geometry"

    def test_validate_plan_not_found(self, valid_csv_file):
        """Test validation when plan is not found in database.

        Args:
            valid_csv_file: Valid CSV file fixture.
        """
        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert len(importer.results) == 1
        assert importer.results[0]["result_type"] == "plan_not_found"

    def test_validate_decision_id_mismatch(self, valid_csv_file, test_plan):
        """Test validation when decision_id doesn't match.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        # Update test plan with different decision_id
        test_plan.decision_id = "2024-999"
        test_plan.save()

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert importer.results[0]["result_type"] == "decision_id_mismatch"

    def test_validate_drawing_number_partial_match(self, valid_csv_file, test_plan):
        """Test drawing number partial match (first 4 chars).

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert importer.results[0]["result_type"] == "success"
        assert importer.results[0]["should_merge_drawing_numbers"] is True

    def test_validate_drawing_number_exact_match(self, tmp_path, test_plan):
        """Test drawing number exact match.

        Args:
            tmp_path: Pytest temporary path fixture.
            test_plan: Test plan fixture.
        """
        csv_path = tmp_path / "exact_match.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "7000", "2024-100", "HEL 2024-12345"])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()
        importer.validate_and_process_rows()

        assert importer.results[0]["result_type"] == "success"
        assert importer.results[0]["should_merge_drawing_numbers"] is True

    def test_update_plans_dry_run(self, valid_csv_file, test_plan):
        """Test dry run mode doesn't modify database.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        original_location = test_plan.location

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        summary = importer.update_plans(dry_run=True)

        assert summary["updated"] == 1
        assert summary["total_rows"] == 1

        test_plan.refresh_from_db()
        assert test_plan.location == original_location

    def test_update_plans_actual_update(self, valid_csv_file, test_plan):
        """Test actual plan update modifies database.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        test_plan.location = None
        test_plan.save()

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        summary = importer.update_plans(dry_run=False)

        assert summary["updated"] == 1

        test_plan.refresh_from_db()
        assert test_plan.location is not None
        assert test_plan.derive_location is False

    def test_update_plans_merges_drawing_numbers(self, valid_csv_file, test_plan):
        """Test that drawing numbers are merged with partial matches replaced.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        importer.update_plans(dry_run=False)

        test_plan.refresh_from_db()
        # CSV has "6593", DB has "6593-3" and "7000"
        # Result: "6593" replaces "6593-3", "7000" is preserved
        assert "6593" in test_plan.drawing_numbers
        assert "6593-3" not in test_plan.drawing_numbers  # Should be replaced
        assert "7000" in test_plan.drawing_numbers  # Should be preserved
        assert len(test_plan.drawing_numbers) == 2

    def test_update_plans_merges_multiple_csv_drawing_numbers(self, tmp_path, test_plan):
        """Test merging multiple comma-separated drawing numbers from CSV.

        Example: CSV has "1234, 4567", DB has "1234-4, 6789"
        Result should be "1234" (replaces 1234-4), "4567" (new), "6789" (preserved)

        Args:
            tmp_path: Pytest temporary path fixture.
            test_plan: Test plan fixture.
        """
        csv_path = tmp_path / "multi_drawing.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        # Set up plan with specific drawing numbers
        test_plan.drawing_numbers = ["1234-4", "6789"]
        test_plan.save()

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            # CSV has comma-separated drawing numbers
            writer.writerow([wkt, "101", "1234, 4567", "2024-100", "HEL 2024-12345"])

        importer = PlanGeometryImporter(str(csv_path))
        importer.parse_csv()
        importer.validate_and_process_rows()
        importer.update_plans(dry_run=False)

        test_plan.refresh_from_db()
        # Result: 1234 (replaces 1234-4), 4567 (new), 6789 (preserved)
        assert "1234" in test_plan.drawing_numbers
        assert "1234-4" not in test_plan.drawing_numbers  # Should be replaced
        assert "4567" in test_plan.drawing_numbers
        assert "6789" in test_plan.drawing_numbers
        assert len(test_plan.drawing_numbers) == 3

    def test_update_plans_skips_matching_geometry(self, valid_csv_file, test_plan):
        """Test that update is skipped when geometry matches.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        # Set plan location to match CSV
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )
        geom = GEOSGeometry(wkt, srid=settings.SRID)

        test_plan.location = get_3d_geometry(geom, 0.0)
        test_plan.derive_location = False
        # Set to what CSV will result in: 6593 (from CSV, replaces 6593-3), 7000 (preserved)
        test_plan.drawing_numbers = ["6593", "7000"]
        test_plan.save()

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        importer.update_plans(dry_run=False)

        # Check for skipped result
        results = importer.get_results()
        assert results[0]["result_type"] == "skipped_no_changes"

    def test_generate_csv_reports(self, tmp_path, valid_csv_file, test_plan):
        """Test CSV report generation.

        Args:
            tmp_path: Pytest temporary path fixture.
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        output_dir = tmp_path / "reports"

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        importer.update_plans(dry_run=False)
        importer.generate_csv_reports(str(output_dir))

        assert output_dir.exists()
        assert (output_dir / "all_results.csv").exists()
        assert (output_dir / "plans_updated.csv").exists()
        assert (output_dir / "plans_updated_detailed.csv").exists()

    def test_get_results_includes_update_details(self, valid_csv_file, test_plan):
        """Test that results include update details after actual update.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        test_plan.location = None
        test_plan.save()

        importer = PlanGeometryImporter(valid_csv_file)
        importer.parse_csv()
        importer.validate_and_process_rows()
        importer.update_plans(dry_run=False)
        results = importer.get_results()

        assert len(results) == 1
        assert "update_details" in results[0]
        assert "fields_changed" in results[0]["update_details"]
        assert len(results[0]["update_details"]["fields_changed"]) > 0
