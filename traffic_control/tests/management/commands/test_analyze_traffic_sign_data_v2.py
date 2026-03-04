"""Tests for TrafficSignAnalyzerV2 and analyze_traffic_sign_data_v2 management command."""
import os

import pytest
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data import TrafficSignAnalyzerV2
from traffic_control.models import MountType, TrafficControlDeviceType

BASE_PATH = os.path.dirname(__file__)
TEST_FILES_DIR = os.path.join(BASE_PATH, "../../test_datas/traffic_sign_import_v2")


def _create_db_entries():
    """Create necessary database entries for tests."""
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")

    # Create device types with codes used in test data
    device_codes = ["C39", "C40", "H24S", "H24", "645", "511", "5111", "5112", "E1", "E1_2"]
    for code in device_codes:
        TrafficControlDeviceType.objects.get_or_create(code=code)


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_basic():
    """Test that TrafficSignAnalyzerV2 can load and analyze CSV files."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")

    analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=",")

    # Verify CSV data was loaded
    assert len(analyzer.mounts_by_id) > 0
    assert len(analyzer.signs_by_id) > 0
    assert len(analyzer.additional_signs_by_id) > 0

    # Verify status segregation
    assert "New" in analyzer.mounts_by_status
    assert "Unchanged" in analyzer.signs_by_status
    assert "Changed" in analyzer.signs_by_status
    assert "Removed" in analyzer.signs_by_status
    assert "invalid" in analyzer.mounts_by_status


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_reports():
    """Test that TrafficSignAnalyzerV2 generates all expected reports."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")

    analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=",")
    reports = analyzer.analyze()

    # Verify we get all expected report types
    report_types = [report["REPORT_TYPE"] for report in reports]

    # Existing report types
    assert "NON EXISTING MOUNTS FOR SIGNS" in report_types
    assert "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS" in report_types
    assert "MOUNT DISTANCES" in report_types
    assert "SIGN DISTANCES" in report_types
    assert "ADDITIONAL SIGN DISTANCES" in report_types
    assert "MOUNTLESS SIGNS" in report_types
    assert "MOUNTLESS ADDITIONAL SIGNS" in report_types
    assert "SIGNLESS ADDITIONAL SIGNS" in report_types

    # New V2 report types
    assert "STATUS DISTRIBUTION" in report_types
    assert "INVALID STATUS VALUES" in report_types
    assert "CHANGE RECORDS" in report_types
    assert "REMOVE RECORDS" in report_types
    assert "REMOVE WITH INVALID LOCATION" in report_types
    assert "TIMESTAMP FORMAT ERRORS" in report_types
    assert "DUPLICATE SIGNS ON SAME MOUNT" in report_types
    assert "ADDED DOUBLE SIDED ZEBRA CROSSINGS" in report_types


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_status_distribution():
    """Test status distribution report contains expected data."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")

    analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=",")
    reports = analyzer.analyze()

    # Find status distribution report
    status_report = next(r for r in reports if r["REPORT_TYPE"] == "STATUS DISTRIBUTION")
    results = status_report["results"]

    # Verify we have stats for all object types and statuses
    assert len(results) > 0

    # Check that results contain expected fields
    for result in results:
        assert "object_type" in result
        assert "status" in result
        assert "count" in result
        assert "percentage" in result


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_duplicate_detection():
    """Test duplicate signs on same mount detection."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")

    analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=",")
    reports = analyzer.analyze()

    # Find duplicate signs report
    duplicate_report = next(r for r in reports if r["REPORT_TYPE"] == "DUPLICATE SIGNS ON SAME MOUNT")
    results = duplicate_report["results"]

    # We should find duplicates (duplicate_sign_1 and duplicate_sign_2 both have C39 on mount_pylvas1)
    assert len(results) > 0

    # Verify duplicate has expected structure
    duplicate = results[0]
    assert "mount_source_id" in duplicate
    assert "device_type_id" in duplicate
    assert "sign_count" in duplicate
    assert duplicate["sign_count"] >= 2


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_zebra_crossings():
    """Test double-sided zebra crossing detection."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")

    analyzer = TrafficSignAnalyzerV2(mount_file, sign_file, delimiter=",")
    reports = analyzer.analyze()

    # Find zebra crossing report
    zebra_report = next(r for r in reports if r["REPORT_TYPE"] == "ADDED DOUBLE SIDED ZEBRA CROSSINGS")
    results = zebra_report["results"]

    # We should find the double-sided zebra crossing (zebra_left_1 and zebra_right_1 are 180° apart)
    assert len(results) > 0

    # Verify zebra crossing pair has expected structure
    zebra = results[0]
    assert "mount_source_id" in zebra
    assert "sign_source_ids" in zebra
    assert len(zebra["sign_source_ids"]) == 2
    assert "directions" in zebra
    assert "direction_difference" in zebra
    # Should be approximately 180 degrees
    assert abs(zebra["direction_difference"] - 180) <= 20


@pytest.mark.django_db
def test_management_command_analyze_traffic_sign_data_v2(tmp_path):
    """Test the analyze_traffic_sign_data_v2 management command."""
    _create_db_entries()

    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")
    output_dir = str(tmp_path)

    # Run the command
    call_command(
        "analyze_traffic_sign_data_v2",
        mount_file=mount_file,
        sign_file=sign_file,
        output_dir=output_dir,
        delimiter=",",
    )

    # Verify output files were created
    output_files = os.listdir(output_dir)
    assert len(output_files) > 0

    # Check that CSV files were created
    csv_files = [f for f in output_files if f.endswith(".csv")]
    assert len(csv_files) > 0

    # Verify some expected report files exist
    report_patterns = [
        "status_distribution_analysis",
        "duplicate_signs_on_same_mount_analysis",
        "added_double_sided_zebra_crossings_analysis",
    ]

    for pattern in report_patterns:
        matching_files = [f for f in csv_files if pattern in f]
        assert len(matching_files) > 0, f"Expected report with pattern '{pattern}' not found"
