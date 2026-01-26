"""Tests for PlanGeometryImportLog model."""
import pytest
from django.utils import timezone

from traffic_control.models import PlanGeometryImportLog


@pytest.mark.django_db
class TestPlanGeometryImportLog:
    """Tests for PlanGeometryImportLog model."""

    def test_create_log_entry(self):
        """Test creating a log entry with minimal fields."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        assert log.id is not None
        assert log.start_time is not None
        assert log.file_path == "/path/to/file.csv"
        assert log.dry_run is False

    def test_str_representation(self):
        """Test string representation of log entry."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        str_repr = str(log)
        assert "Plan Geometry Import" in str_repr
        assert log.start_time.strftime("%Y-%m-%d %H:%M:%S") in str_repr

    def test_total_rows_property(self):
        """Test total_rows property calculation."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
            results=[
                {"result_type": "success"},
                {"result_type": "plan_not_found"},
                {"result_type": "invalid_wkt"},
            ],
        )

        assert log.total_rows == 3

    def test_total_rows_empty_results(self):
        """Test total_rows property with empty results."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        assert log.total_rows == 0

    def test_success_count_property(self):
        """Test success_count property calculation."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
            results=[
                {"result_type": "success"},
                {"result_type": "success"},
                {"result_type": "plan_not_found"},
            ],
        )

        assert log.success_count == 2

    def test_skipped_count_property(self):
        """Test skipped_count property calculation."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
            results=[
                {"result_type": "success"},
                {"result_type": "skipped_no_changes"},
                {"result_type": "skipped_no_changes"},
                {"result_type": "plan_not_found"},
            ],
        )

        assert log.skipped_count == 2

    def test_error_count_property(self):
        """Test error_count property excludes success and skipped."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
            results=[
                {"result_type": "success"},
                {"result_type": "skipped_no_changes"},
                {"result_type": "plan_not_found"},
                {"result_type": "invalid_wkt"},
                {"result_type": "invalid_geometry_type"},
            ],
        )

        assert log.error_count == 3

    def test_results_json_field(self):
        """Test results field stores complex JSON data."""
        results_data = [
            {
                "row_number": 1,
                "diaari": "HEL 2024-12345",
                "result_type": "success",
                "plan_id": "uuid-here",
                "update_details": {
                    "csv_row": 1,
                    "plan_id": "uuid-here",
                    "diary_number": "HEL 2024-12345",
                    "fields_changed": [
                        {
                            "field": "location",
                            "old_value": "None",
                            "new_value": "MULTIPOLYGON...",
                        }
                    ],
                },
            }
        ]

        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
            results=results_data,
        )

        log.refresh_from_db()
        assert log.results == results_data
        assert log.results[0]["update_details"]["fields_changed"][0]["field"] == "location"

    def test_dry_run_flag(self):
        """Test dry_run flag is stored correctly."""
        log_dry = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=True,
        )

        log_actual = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        assert log_dry.dry_run is True
        assert log_actual.dry_run is False

    def test_end_time_can_be_null(self):
        """Test end_time can be null for in-progress imports."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        assert log.end_time is None

    def test_end_time_can_be_set(self):
        """Test end_time can be set after completion."""
        log = PlanGeometryImportLog.objects.create(
            start_time=timezone.now(),
            file_path="/path/to/file.csv",
            output_dir="/path/to/output",
            dry_run=False,
        )

        end = timezone.now()
        log.end_time = end
        log.save()

        log.refresh_from_db()
        assert log.end_time == end
