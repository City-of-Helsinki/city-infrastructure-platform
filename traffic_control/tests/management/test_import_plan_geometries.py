"""Tests for import_plan_geometries management command."""
import csv
from io import StringIO

import pytest
from django.core.management import call_command

from traffic_control.models import PlanGeometryImportLog
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
    """Create a test plan.

    Args:
        db: Pytest database fixture.
        test_user: Test user fixture.

    Returns:
        Plan: Test plan instance.
    """
    return PlanFactory(
        diary_number="HEL 2024-12345",
        decision_id="2024-100",
        drawing_numbers=["6593-3"],
        created_by=test_user,
        updated_by=test_user,
    )


@pytest.fixture
def test_plan_2(db, test_user):
    """Create a second test plan.

    Args:
        db: Pytest database fixture.
        test_user: Test user fixture.

    Returns:
        Plan: Test plan instance.
    """
    return PlanFactory(
        diary_number="HEL 2024-99999",
        decision_id="2024-200",
        drawing_numbers=["7000"],
        created_by=test_user,
        updated_by=test_user,
    )


@pytest.fixture
def valid_csv_file(tmp_path):
    """Create a valid CSV file.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to created CSV file.
    """
    csv_path = tmp_path / "test_geometries.csv"
    wkt = (
        "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
        "25493859.07 6679719.85, 25493824.78 6679773.23)))"
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
        writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])

    return csv_path


@pytest.fixture
def multiple_plans(db, test_user):
    """Create multiple test plans for batch testing.

    Args:
        db: Pytest database fixture.
        test_user: Test user fixture.

    Returns:
        list: List of Plan instances.
    """
    plans = []
    for i in range(15):
        plan = PlanFactory(
            diary_number=f"HEL 2024-{12345+i}",
            decision_id="2024-100",
            drawing_numbers=["6593-3"],
            created_by=test_user,
            updated_by=test_user,
        )
        plan.location = None
        plan.save()
        plans.append(plan)
    return plans


@pytest.fixture
def multiple_rows_csv(tmp_path):
    """Create CSV with multiple rows for testing update details display.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        Path: Path to created CSV file.
    """
    csv_path = tmp_path / "multiple_rows.csv"
    wkt = (
        "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
        "25493859.07 6679719.85, 25493824.78 6679773.23)))"
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
        # Add 15 rows with unique diary numbers
        for i in range(15):
            writer.writerow([wkt, f"{101+i}", "6593", "2024-100", f"HEL 2024-{12345+i}"])

    return csv_path


@pytest.mark.django_db(transaction=True)
class TestImportPlanGeometriesCommand:
    """Tests for import_plan_geometries management command."""

    def test_command_with_valid_file(self, valid_csv_file, test_plan, tmp_path):
        """Test command executes successfully with valid file.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Starting plan geometry import" in output
        assert "Parsing CSV file..." in output
        assert "Validating geometries and matching plans..." in output
        assert "Updating plans..." in output
        assert "Successfully updated: 1" in output
        assert output_dir.exists()

    def test_command_dry_run(self, valid_csv_file, test_plan, tmp_path):
        """Test command dry run mode.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        test_plan.location = None
        test_plan.save()

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            "--dry-run",
            stdout=out,
        )

        output = out.getvalue()
        assert "DRY RUN MODE" in output
        assert "Simulating updates..." in output

        test_plan.refresh_from_db()
        assert test_plan.location is None

    def test_command_no_csv_flag(self, valid_csv_file, test_plan, tmp_path):
        """Test command with --no-csv flag.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            "--no-csv",
            stdout=out,
        )

        output = out.getvalue()
        assert "Skipping CSV report generation" in output
        assert "CSV reports were not generated" in output
        assert not (output_dir / "all_results.csv").exists()

    def test_command_creates_log_entry(self, valid_csv_file, test_plan, tmp_path):
        """Test command creates PlanGeometryImportLog entry.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"
        initial_count = PlanGeometryImportLog.objects.count()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            stdout=StringIO(),
        )

        assert PlanGeometryImportLog.objects.count() == initial_count + 1

        log = PlanGeometryImportLog.objects.latest("start_time")
        assert log.file_path == str(valid_csv_file.absolute())
        assert log.output_dir == str(output_dir.absolute())
        assert log.start_time is not None
        assert log.end_time is not None
        assert log.results is not None
        assert len(log.results) == 1
        assert log.dry_run is False

    def test_command_file_not_found(self, tmp_path):
        """Test command handles missing file gracefully.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"
        err = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            "/nonexistent/file.csv",
            "--output-dir",
            str(output_dir),
            stderr=err,
        )

        error_output = err.getvalue()
        assert "File not found" in error_output

    def test_command_displays_summary_statistics(self, valid_csv_file, test_plan, tmp_path):
        """Test command displays summary statistics.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Import Summary" in output
        assert "Total rows processed: 1" in output
        assert "Successfully updated:" in output
        assert "Detailed results saved to database" in output
        assert "CSV reports saved to:" in output

    def test_command_displays_update_details(self, valid_csv_file, test_plan, tmp_path):
        """Test command displays update details for successful updates.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        test_plan.location = None
        test_plan.save()

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Update Details" in output
        assert "CSV Row 1:" in output
        assert "Plan ID:" in output
        assert "Diary Number:" in output
        assert "Fields updated:" in output
        assert "location:" in output

    def test_command_no_update_details_on_dry_run(self, valid_csv_file, test_plan, tmp_path):
        """Test that update details are not shown in dry-run mode.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        test_plan.location = None
        test_plan.save()

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            "--dry-run",
            stdout=out,
        )

        output = out.getvalue()
        assert "Update Details" not in output

    def test_command_displays_first_10_updates(self, multiple_rows_csv, multiple_plans, tmp_path):
        """Test command shows only first 10 updates with message about more.

        Args:
            multiple_rows_csv: CSV with multiple rows fixture.
            multiple_plans: Multiple test plans fixture.
            tmp_path: Pytest temporary path fixture.
        """

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(multiple_rows_csv),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Update Details" in output
        assert "Showing first 10 of 15 updates" in output
        assert "See database log for complete details" in output

    def test_command_default_output_dir(self, valid_csv_file, test_plan):
        """Test command uses default output directory when not specified.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
        """
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            stdout=out,
        )

        output = out.getvalue()
        assert "Starting plan geometry import" in output
        assert "plan_geometry_import_results" in output

    def test_command_multiple_errors_breakdown(self, tmp_path):
        """Test command displays error breakdown for multiple error types.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "errors.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", ""])  # Missing diary
            writer.writerow(["INVALID", "102", "6593", "2024-100", "HEL 2024-99999"])  # Invalid WKT

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(csv_path),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Error Breakdown" in output
        assert "missing_diary_number:" in output
        assert "invalid_wkt:" in output

    def test_command_skipped_count_displayed(self, tmp_path, test_plan):
        """Test command displays skipped count when geometries match.

        Args:
            tmp_path: Pytest temporary path fixture.
            test_plan: Test plan fixture.
        """
        # Set plan with matching geometry
        from django.conf import settings
        from django.contrib.gis.geos import GEOSGeometry

        from traffic_control.geometry_utils import get_3d_geometry

        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )
        geom = GEOSGeometry(wkt, srid=settings.SRID)
        test_plan.location = get_3d_geometry(geom, 0.0)
        test_plan.derive_location = False
        # Set to what CSV will result in: 6593 (from CSV, no partial match to replace)
        test_plan.drawing_numbers = ["6593"]
        test_plan.save()

        csv_path = tmp_path / "skipped.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-12345"])

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(csv_path),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Skipped (no changes): 1" in output

    def test_command_empty_csv_file(self, tmp_path):
        """Test command handles empty CSV file.

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "empty.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            # No data rows

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(csv_path),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "No data rows found in CSV" in output

        log = PlanGeometryImportLog.objects.latest("start_time")
        assert log.results == []

    def test_command_with_errors_only(self, tmp_path):
        """Test command when all rows have errors (no successes).

        Args:
            tmp_path: Pytest temporary path fixture.
        """
        csv_path = tmp_path / "all_errors.csv"
        wkt = (
            "MULTIPOLYGON (((25493824.78 6679773.23, 25493870.36 6679749.80, "
            "25493859.07 6679719.85, 25493824.78 6679773.23)))"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["wkt_geom", "fid", "piirustusnumero", "decision_id", "diaari"])
            writer.writerow([wkt, "101", "6593", "2024-100", "HEL 2024-NOTFOUND"])

        output_dir = tmp_path / "output"
        out = StringIO()

        call_command(
            "import_plan_geometries",
            "--file",
            str(csv_path),
            "--output-dir",
            str(output_dir),
            stdout=out,
        )

        output = out.getvalue()
        assert "Successfully updated: 0" in output
        assert "Errors encountered: 1" in output
        assert "Error Breakdown" in output
        assert "Update Details" not in output

    def test_command_log_stores_dry_run_flag(self, valid_csv_file, test_plan, tmp_path):
        """Test that log entry correctly stores dry_run flag.

        Args:
            valid_csv_file: Valid CSV file fixture.
            test_plan: Test plan fixture.
            tmp_path: Pytest temporary path fixture.
        """
        output_dir = tmp_path / "output"

        call_command(
            "import_plan_geometries",
            "--file",
            str(valid_csv_file),
            "--output-dir",
            str(output_dir),
            "--dry-run",
            stdout=StringIO(),
        )

        log = PlanGeometryImportLog.objects.latest("start_time")
        assert log.dry_run is True
