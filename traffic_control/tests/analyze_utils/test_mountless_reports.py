"""Tests for the mountless report methods in ReportsMixin."""

from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2
from traffic_control.analyze_utils.traffic_sign_data_v2_reports import ReportsMixin


def _make_mount(
    mount_id: str,
    status: str = "New",
    ssurl: str = "",
    mount_type: str = "pole",
) -> dict:
    """Build a minimal mount CSV row dict for testing."""
    return {
        CSVHeadersV2.id: mount_id,
        CSVHeadersV2.status: status,
        CSVHeadersV2.attachment_url: ssurl,
        CSVHeadersV2.mount_type: mount_type,
    }


def _make_sign(
    sign_id: str,
    mount_id: str,
    status: str = "New",
    code: str = "A1",
    ssurl: str = "",
) -> dict:
    """Build a minimal sign CSV row dict for testing."""
    return {
        CSVHeadersV2.id: sign_id,
        CSVHeadersV2.mount_id: mount_id,
        CSVHeadersV2.status: status,
        CSVHeadersV2.code: code,
        CSVHeadersV2.attachment_url: ssurl,
    }


class _StubAnalyzer(ReportsMixin):
    """Minimal stub that satisfies ReportsMixin attribute requirements."""

    def __init__(self, mounts_by_id: dict, signs_by_id: dict) -> None:
        self.mounts_by_id = mounts_by_id
        self.signs_by_id = signs_by_id
        self.additional_signs_by_id = {}
        self.signposts_by_id = {}


# ==================== _is_mountless ====================


def test_is_mountless_blank_mount_id() -> None:
    """Signs with a blank mount_id are considered mountless."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    assert analyzer._is_mountless("") is True
    assert analyzer._is_mountless("   ") is True


def test_is_mountless_mount_not_in_csv() -> None:
    """Signs referencing a mount that does not exist in CSV are considered mountless."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    assert analyzer._is_mountless("M-999") is True


def test_is_mountless_mount_has_removed_status() -> None:
    """Signs whose referenced mount has status Removed are considered mountless."""
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": _make_mount("M-1", status="Removed")},
        signs_by_id={},
    )
    assert analyzer._is_mountless("M-1") is True


def test_is_mountless_valid_active_mount() -> None:
    """Signs with a valid, non-Removed mount are NOT considered mountless."""
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": _make_mount("M-1", status="New")},
        signs_by_id={},
    )
    assert analyzer._is_mountless("M-1") is False


# ==================== _build_mountless_report ====================


def test_build_mountless_report_excludes_removed_objects() -> None:
    """Objects with status Removed must be excluded from the mountless report."""
    sign = _make_sign("S-1", mount_id="", status="Removed")
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={"S-1": sign})
    report = analyzer._build_mountless_report({"S-1": sign}, "MOUNTLESS SIGNS", "sign_source_id")
    assert report["results"] == []


def test_build_mountless_report_excludes_objects_with_valid_mount() -> None:
    """Objects that reference an active mount must not appear in the report."""
    mount = _make_mount("M-1", status="New")
    sign = _make_sign("S-1", mount_id="M-1", status="New")
    analyzer = _StubAnalyzer(mounts_by_id={"M-1": mount}, signs_by_id={"S-1": sign})
    report = analyzer._build_mountless_report({"S-1": sign}, "MOUNTLESS SIGNS", "sign_source_id")
    assert report["results"] == []


def test_build_mountless_report_blank_mount_id_no_mount_in_csv() -> None:
    """Signs with blank mount_id and no mount in CSV appear; mount_ssurl and mount_type are empty strings."""
    sign = _make_sign("S-1", mount_id="", status="New", code="B4", ssurl="http://sign-url")
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={"S-1": sign})
    report = analyzer._build_mountless_report({"S-1": sign}, "MOUNTLESS SIGNS", "sign_source_id")

    assert report["REPORT_TYPE"] == "MOUNTLESS SIGNS"
    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["sign_source_id"] == "S-1"
    assert result["status"] == "New"
    assert result["mount_id"] == "does not exist"
    assert result["mount_status"] == "does not exist"
    assert result["object_ssurl"] == "http://sign-url"
    assert result["mount_ssurl"] == ""
    assert result["devicetype_code"] == "B4"
    assert result["mount_type"] == ""


def test_build_mountless_report_removed_mount_provides_ssurl_and_type() -> None:
    """When referenced mount exists but is Removed, its ssurl and mount_type are included."""
    mount = _make_mount("M-1", status="Removed", ssurl="http://mount-url", mount_type="wall")
    sign = _make_sign("S-1", mount_id="M-1", status="New", code="C3", ssurl="http://sign-url")
    analyzer = _StubAnalyzer(mounts_by_id={"M-1": mount}, signs_by_id={"S-1": sign})
    report = analyzer._build_mountless_report({"S-1": sign}, "MOUNTLESS SIGNS", "sign_source_id")

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["mount_id"] == "M-1"
    assert result["mount_status"] == "Removed"
    assert result["mount_ssurl"] == "http://mount-url"
    assert result["mount_type"] == "wall"
    assert result["object_ssurl"] == "http://sign-url"
    assert result["devicetype_code"] == "C3"


def test_build_mountless_report_mount_not_in_csv_empty_strings() -> None:
    """When mount_id is set but mount does not exist in CSV, mount_ssurl and mount_type are empty."""
    sign = _make_sign("S-2", mount_id="M-GHOST", status="Unchanged", code="D5", ssurl="http://s2")
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={"S-2": sign})
    report = analyzer._build_mountless_report({"S-2": sign}, "MOUNTLESS SIGNS", "sign_source_id")

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["mount_id"] == "does not exist"
    assert result["mount_status"] == "does not exist"
    assert result["mount_ssurl"] == ""
    assert result["mount_type"] == ""
    assert result["devicetype_code"] == "D5"
    assert result["object_ssurl"] == "http://s2"


def test_build_mountless_report_id_key_used_correctly() -> None:
    """The id_key parameter controls which key the source_id is stored under."""
    sign = _make_sign("AS-1", mount_id="", status="New")
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    report = analyzer._build_mountless_report(
        {"AS-1": sign},
        "MOUNTLESS ADDITIONAL SIGNS",
        "additional_sign_source_id",
    )
    assert "additional_sign_source_id" in report["results"][0]
    assert report["results"][0]["additional_sign_source_id"] == "AS-1"


def test_build_mountless_report_multiple_objects_mixed() -> None:
    """Only objects that are mountless and not Removed appear in the report."""
    mount_active = _make_mount("M-OK", status="New")
    mount_removed = _make_mount("M-DEL", status="Removed", ssurl="http://mdel", mount_type="bracket")
    sign_valid = _make_sign("S-valid", mount_id="M-OK", status="New")
    sign_removed = _make_sign("S-removed", mount_id="", status="Removed")
    sign_mountless_no_csv = _make_sign("S-nocsvmount", mount_id="M-MISSING", status="New", code="X1", ssurl="http://x1")
    sign_mountless_deleted = _make_sign("S-delmount", mount_id="M-DEL", status="New", code="X2", ssurl="http://x2")

    objects = {
        "S-valid": sign_valid,
        "S-removed": sign_removed,
        "S-nocsvmount": sign_mountless_no_csv,
        "S-delmount": sign_mountless_deleted,
    }
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-OK": mount_active, "M-DEL": mount_removed},
        signs_by_id=objects,
    )
    report = analyzer._build_mountless_report(objects, "MOUNTLESS SIGNS", "sign_source_id")
    result_ids = {r["sign_source_id"] for r in report["results"]}

    assert result_ids == {"S-nocsvmount", "S-delmount"}

    no_csv_result = next(r for r in report["results"] if r["sign_source_id"] == "S-nocsvmount")
    assert no_csv_result["mount_id"] == "does not exist"
    assert no_csv_result["mount_ssurl"] == ""
    assert no_csv_result["mount_type"] == ""
    assert no_csv_result["devicetype_code"] == "X1"

    del_result = next(r for r in report["results"] if r["sign_source_id"] == "S-delmount")
    assert del_result["mount_id"] == "M-DEL"
    assert del_result["mount_ssurl"] == "http://mdel"
    assert del_result["mount_type"] == "bracket"
    assert del_result["devicetype_code"] == "X2"


# ==================== _get_mountless_signs / _get_mountless_additional_signs / _get_mountless_signposts
# ====================


def test_get_mountless_signs_report_type() -> None:
    """_get_mountless_signs returns correct REPORT_TYPE."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    report = analyzer._get_mountless_signs()
    assert report["REPORT_TYPE"] == "MOUNTLESS SIGNS"


def test_get_mountless_additional_signs_report_type() -> None:
    """_get_mountless_additional_signs returns correct REPORT_TYPE."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    report = analyzer._get_mountless_additional_signs()
    assert report["REPORT_TYPE"] == "MOUNTLESS ADDITIONAL SIGNS"


def test_get_mountless_signposts_report_type() -> None:
    """_get_mountless_signposts returns correct REPORT_TYPE."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={})
    report = analyzer._get_mountless_signposts()
    assert report["REPORT_TYPE"] == "MOUNTLESS SIGNPOSTS"


def test_get_mountless_signs_uses_signs_by_id() -> None:
    """_get_mountless_signs reads from signs_by_id and produces expected result fields."""
    sign = _make_sign("S-10", mount_id="", status="New", code="E5", ssurl="http://e5")
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_id={"S-10": sign})
    report = analyzer._get_mountless_signs()

    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["sign_source_id"] == "S-10"
    assert result["devicetype_code"] == "E5"
    assert result["object_ssurl"] == "http://e5"
    assert result["mount_id"] == "does not exist"
    assert result["mount_ssurl"] == ""
    assert result["mount_type"] == ""
    assert result["mount_status"] == "does not exist"
