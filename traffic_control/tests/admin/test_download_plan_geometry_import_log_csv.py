"""Tests for PlanGeometryImportLogAdmin custom CSV download views."""
import csv
from io import StringIO

import pytest
from django.urls import reverse
from django.utils import timezone

from traffic_control.models import PlanGeometryImportLog


@pytest.fixture
def import_log(db):
    """Create a PlanGeometryImportLog with predetermined JSON results for testing.

    Includes one successful row with geometry updates, and one error row.
    """
    results = [
        {
            "row_number": 1,
            "diaari": "HEL 2024-001",
            "fid": "101",
            "piirustusnumero": "1234",
            "decision_id": "DEC-1",
            "result_type": "success",
            "plan_id": "PLAN-001",
            "update_details": {
                "fields_changed": [
                    {"field": "location", "old_value": "None", "new_value": "MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))"},
                    {"field": "decision_id", "old_value": "OLD-DEC", "new_value": "DEC-1"},
                ]
            },
        },
        {
            "row_number": 2,
            "diaari": "",
            "fid": "102",
            "piirustusnumero": "5678",
            "decision_id": "DEC-2",
            "result_type": "missing_diary_number",
            "error_message": "Diary number is required but missing.",
        },
    ]

    return PlanGeometryImportLog.objects.create(
        start_time=timezone.now(),
        end_time=timezone.now(),
        file_path="/tmp/test.csv",
        output_dir="/tmp/out",
        dry_run=False,
        results=results,
    )


@pytest.mark.django_db
class TestPlanGeometryImportLogAdminCSVDownload:
    def _parse_csv_response(self, response):
        """Helper to decode and parse the CSV response."""
        # Decode using 'utf-8-sig' to automatically consume the \ufeff BOM
        content = response.content.decode("utf-8-sig")
        reader = csv.reader(StringIO(content), delimiter=";")
        return list(reader)

    def test_download_success_summary_csv(self, admin_client, import_log):
        """Test downloading the summary CSV for successful imports."""
        url = reverse(
            "admin:traffic_control_plangeometryimportlog_download_csv",
            args=[import_log.id, "success"],
            query={"mode": "summary"},
        )
        response = admin_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv; charset=utf-8"
        assert 'filename="plan_import_success_' in response["Content-Disposition"]

        rows = self._parse_csv_response(response)

        # Check Headers
        assert rows[0] == ["Row", "Diary Number", "FID", "Drawing #", "Decision ID", "Plan ID", "Fields Changed"]

        # Check Data Row 1 (Success Data)
        # In summary mode, EWKT should be reduced to polygon counts, and separated by "; "
        assert rows[1] == [
            "1",
            "HEL 2024-001",
            "101",
            "1234",
            "DEC-1",
            "PLAN-001",
            "location: None → MultiPolygon (1 polygons); decision_id: OLD-DEC → DEC-1",
        ]

    def test_download_success_detailed_csv(self, admin_client, import_log):
        """Test downloading the detailed CSV for successful imports."""
        url = reverse(
            "admin:traffic_control_plangeometryimportlog_download_csv",
            args=[import_log.id, "success"],
            query={"mode": "detailed"},
        )
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'filename="plan_import_success_detailed_' in response["Content-Disposition"]

        rows = self._parse_csv_response(response)

        # Check Headers
        assert rows[0] == ["Row", "Diary Number", "FID", "Drawing #", "Decision ID", "Plan ID", "Fields Changed"]

        # Check Data Row 1 (Success Data)
        # In detailed mode, full EWKT should be present, separated by " | "
        assert rows[1] == [
            "1",
            "HEL 2024-001",
            "101",
            "1234",
            "DEC-1",
            "PLAN-001",
            "location: None → MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0))) | decision_id: OLD-DEC → DEC-1",
        ]

    def test_download_error_csv(self, admin_client, import_log):
        """Test downloading the CSV for error rows."""
        url = reverse(
            "admin:traffic_control_plangeometryimportlog_download_csv", args=[import_log.id, "missing_diary_number"]
        )
        response = admin_client.get(url)

        assert response.status_code == 200
        assert 'filename="plan_import_missing_diary_number_' in response["Content-Disposition"]

        rows = self._parse_csv_response(response)

        # Check Headers
        assert rows[0] == ["Row", "Diary Number", "FID", "Drawing #", "Decision ID", "Error"]

        # Check Data Row 1 (Error Data)
        assert rows[1] == ["2", "", "102", "5678", "DEC-2", "Diary number is required but missing."]

    def test_download_csv_unauthorized(self, client, import_log):
        """Ensure standard non-admin users/anonymous clients cannot hit this endpoint."""
        url = reverse("admin:traffic_control_plangeometryimportlog_download_csv", args=[import_log.id, "success"])
        # Unauthenticated client
        response = client.get(url)

        # Should redirect to the admin login page
        assert response.status_code == 302
        assert "admin/login" in response.url
