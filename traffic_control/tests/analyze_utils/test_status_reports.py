"""Tests for _get_remove_records_report in StatusReportsMixin."""
from typing import Any

from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2
from traffic_control.analyze_utils.traffic_sign_data_v2_status_reports import StatusReportsMixin


def _make_obj(source_id: str, status: str = "Removed", code: str = "A1") -> dict:
    """Build a minimal CSV row dict for testing.

    Args:
        source_id (str): The source ID of the object.
        status (str): The status field value.
        code (str): The device type code.

    Returns:
        dict: A minimal CSV row dict.
    """
    return {
        CSVHeadersV2.id: source_id,
        CSVHeadersV2.status: status,
        CSVHeadersV2.code: code,
    }


class _StubAnalyzer(StatusReportsMixin):
    """Minimal stub satisfying StatusReportsMixin requirements for remove records tests."""

    def __init__(
        self,
        mounts: list[dict] | None = None,
        signs: list[dict] | None = None,
        additional_signs: list[dict] | None = None,
        signposts: list[dict] | None = None,
        mount_db_ids: set[str] | None = None,
        sign_db_ids: dict[str, Any] | None = None,
        additional_sign_db_ids: dict[str, Any] | None = None,
        signpost_db_ids: dict[str, Any] | None = None,
    ) -> None:
        self.mounts_by_status = {"Removed": mounts or []}
        self.signs_by_status = {"Removed": signs or []}
        self.additional_signs_by_status = {"Removed": additional_signs or []}
        self.signposts_by_status = {"Removed": signposts or []}
        self.mount_reals_by_source_id_set = mount_db_ids or set()
        self.sign_reals_by_source_id = sign_db_ids or {}
        self.additional_sign_reals_by_source_id = additional_sign_db_ids or {}
        self.signpost_reals_by_source_id = signpost_db_ids or {}


# ==================== _get_remove_records_report ====================


def test_remove_records_report_type() -> None:
    """Report must have REPORT_TYPE equal to 'REMOVE RECORDS'."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_remove_records_report()
    assert report["REPORT_TYPE"] == "REMOVE RECORDS"


def test_remove_records_empty_when_no_removed_objects() -> None:
    """Report has empty results when no objects have Removed status."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_remove_records_report()
    assert report["results"] == []


def test_remove_records_mount_found_in_database() -> None:
    """Mount found in database has found_in_database=True and no device_code field."""
    mount = _make_obj("M-1")
    analyzer = _StubAnalyzer(mounts=[mount], mount_db_ids={"M-1"})
    report = analyzer._get_remove_records_report()

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["object_type"] == "mount"
    assert result["mount_source_id"] == "M-1"
    assert result["found_in_database"] is True
    assert "device_code" not in result


def test_remove_records_mount_not_found_in_database() -> None:
    """Mount absent from database has found_in_database=False."""
    mount = _make_obj("M-2")
    analyzer = _StubAnalyzer(mounts=[mount], mount_db_ids=set())
    report = analyzer._get_remove_records_report()

    assert report["results"][0]["found_in_database"] is False


def test_remove_records_sign_found_in_database() -> None:
    """Traffic sign found in database has found_in_database=True and includes device_code."""
    sign = _make_obj("S-1", code="B2")
    analyzer = _StubAnalyzer(signs=[sign], sign_db_ids={"S-1": "some-db-id"})
    report = analyzer._get_remove_records_report()

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["object_type"] == "traffic_sign"
    assert result["sign_source_id"] == "S-1"
    assert result["device_code"] == "B2"
    assert result["found_in_database"] is True


def test_remove_records_sign_not_found_in_database() -> None:
    """Traffic sign absent from database has found_in_database=False."""
    sign = _make_obj("S-2", code="C3")
    analyzer = _StubAnalyzer(signs=[sign], sign_db_ids={})
    report = analyzer._get_remove_records_report()

    assert report["results"][0]["found_in_database"] is False


def test_remove_records_additional_sign_found_in_database() -> None:
    """Additional sign found in database has found_in_database=True and includes device_code."""
    additional_sign = _make_obj("AS-1", code="D4")
    analyzer = _StubAnalyzer(additional_signs=[additional_sign], additional_sign_db_ids={"AS-1": "some-db-id"})
    report = analyzer._get_remove_records_report()

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["object_type"] == "additional_sign"
    assert result["additional_sign_source_id"] == "AS-1"
    assert result["device_code"] == "D4"
    assert result["found_in_database"] is True


def test_remove_records_signpost_not_found_in_database() -> None:
    """Signpost absent from database has found_in_database=False and includes device_code."""
    signpost = _make_obj("SP-1", code="E5")
    analyzer = _StubAnalyzer(signposts=[signpost], signpost_db_ids={})
    report = analyzer._get_remove_records_report()

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["object_type"] == "signpost"
    assert result["signpost_source_id"] == "SP-1"
    assert result["device_code"] == "E5"
    assert result["found_in_database"] is False


def test_remove_records_mixed_object_types_and_db_presence() -> None:
    """All object categories appear in results; found_in_database reflects DB presence correctly."""
    mount = _make_obj("M-10")
    sign = _make_obj("S-10", code="A1")
    additional_sign = _make_obj("AS-10", code="B2")
    signpost = _make_obj("SP-10", code="C3")

    analyzer = _StubAnalyzer(
        mounts=[mount],
        signs=[sign],
        additional_signs=[additional_sign],
        signposts=[signpost],
        mount_db_ids={"M-10"},
        sign_db_ids={},
        additional_sign_db_ids={"AS-10": "some-id"},
        signpost_db_ids={},
    )
    report = analyzer._get_remove_records_report()
    results_by_id = {
        r.get("mount_source_id")
        or r.get("sign_source_id")
        or r.get("additional_sign_source_id")
        or r.get("signpost_source_id"): r
        for r in report["results"]
    }

    assert results_by_id["M-10"]["found_in_database"] is True
    assert results_by_id["S-10"]["found_in_database"] is False
    assert results_by_id["AS-10"]["found_in_database"] is True
    assert results_by_id["SP-10"]["found_in_database"] is False
