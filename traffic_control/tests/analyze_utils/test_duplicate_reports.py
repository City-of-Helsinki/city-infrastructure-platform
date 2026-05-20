"""Tests for duplicate-sign-on-same-mount report methods in ReportsMixin."""

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_constants import (
    CSVHeadersV2,
    DUPLICATE_PAIR_EXCLUDED_CODES,
)
from traffic_control.analyze_utils.traffic_sign_data_v2_reports import ReportsMixin


def _make_mount(mount_id: str, status: str = "New") -> dict:
    """Build a minimal mount CSV row dict for testing.

    Args:
        mount_id (str): Source ID of the mount.
        status (str): Status value for the mount row.

    Returns:
        dict: Minimal mount CSV row dict.
    """
    return {
        CSVHeadersV2.id: mount_id,
        CSVHeadersV2.status: status,
        CSVHeadersV2.attachment_url: "",
        CSVHeadersV2.mount_type: "pole",
        CSVHeadersV2.coord_x: "25496000",
        CSVHeadersV2.coord_y: "6672000",
        CSVHeadersV2.coord_z: "0",
    }


def _make_sign(
    sign_id: str,
    mount_id: str,
    code: str,
    status: str = "New",
    direction: int = 0,
) -> dict:
    """Build a minimal sign CSV row dict for testing.

    Args:
        sign_id (str): Source ID of the sign.
        mount_id (str): Source ID of the mount the sign is attached to.
        code (str): Device type code for the sign.
        status (str): Status value for the sign row.
        direction (int): Azimuth direction in degrees.

    Returns:
        dict: Minimal sign CSV row dict.
    """
    return {
        CSVHeadersV2.id: sign_id,
        CSVHeadersV2.mount_id: mount_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.status: status,
        CSVHeadersV2.direction: str(direction),
        CSVHeadersV2.attachment_url: "",
    }


class _StubAnalyzer(ReportsMixin):
    """Minimal stub satisfying ReportsMixin attribute requirements for duplicate reports."""

    def __init__(
        self,
        mounts_by_id: dict,
        signs_by_mount_id: dict,
        code_to_device_type_id: dict | None = None,
    ) -> None:
        self.mounts_by_id = mounts_by_id
        self.signs_by_mount_id = signs_by_mount_id
        self.code_to_device_type_id = code_to_device_type_id or {}

    def _georeferenced_point_from_csv_row(self, row: dict):  # type: ignore[override]
        """Stub: return None so ewkt is never called in unit tests."""
        return None

    def _get_mount_location_ewkt(self, mount_id: str) -> str | None:  # type: ignore[override]
        """Stub: always return a fixed EWKT string."""
        return "SRID=3879;POINT(25496000 6672000 0)"


# ==================== _is_excluded_duplicate_pair ====================


@pytest.mark.parametrize("code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_is_excluded_duplicate_pair_returns_true_for_two_excluded_code_signs(code: str) -> None:
    """A pair of signs both having an excluded code must be excluded."""
    sign1 = _make_sign("S-1", "M-1", code)
    sign2 = _make_sign("S-2", "M-1", code)
    assert ReportsMixin._is_excluded_duplicate_pair([sign1, sign2]) is True


def test_is_excluded_duplicate_pair_returns_false_for_mixed_excluded_codes() -> None:
    """A pair where each sign has a different excluded code must NOT be excluded."""
    codes = sorted(DUPLICATE_PAIR_EXCLUDED_CODES)
    sign1 = _make_sign("S-1", "M-1", codes[0])
    sign2 = _make_sign("S-2", "M-1", codes[1])
    assert ReportsMixin._is_excluded_duplicate_pair([sign1, sign2]) is False


def test_is_excluded_duplicate_pair_returns_false_for_non_excluded_code() -> None:
    """A pair where at least one sign has a non-excluded code must NOT be excluded."""
    sign1 = _make_sign("S-1", "M-1", "5111")
    sign2 = _make_sign("S-2", "M-1", "A1")
    assert ReportsMixin._is_excluded_duplicate_pair([sign1, sign2]) is False


@pytest.mark.parametrize("code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_is_excluded_duplicate_pair_returns_false_for_three_excluded_code_signs(code: str) -> None:
    """Three signs with excluded codes must NOT be excluded (count != 2)."""
    signs = [_make_sign(f"S-{i}", "M-1", code) for i in range(3)]
    assert ReportsMixin._is_excluded_duplicate_pair(signs) is False


def test_is_excluded_duplicate_pair_returns_false_for_empty_list() -> None:
    """An empty group must NOT be excluded."""
    assert ReportsMixin._is_excluded_duplicate_pair([]) is False


# ==================== _get_duplicate_signs_on_same_mount ====================


def _make_stub_with_two_signs(code: str, same_device_type_id: str = "dt-1") -> _StubAnalyzer:
    """Build a stub with two signs of the given code on the same mount.

    Args:
        code (str): Device type code to assign to both signs.
        same_device_type_id (str): Device type ID both codes map to.

    Returns:
        _StubAnalyzer: Configured stub analyzer.
    """
    mount = _make_mount("M-1")
    signs = [_make_sign(f"S-{i}", "M-1", code) for i in range(2)]
    return _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={code: same_device_type_id},
    )


@pytest.mark.parametrize("code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_duplicate_report_excludes_pair_of_excluded_code_signs(code: str) -> None:
    """A mount with exactly 2 signs of an excluded code produces no results."""
    analyzer = _make_stub_with_two_signs(code)
    report = analyzer._get_duplicate_signs_on_same_mount(exact_code_match=False)
    assert report["results"] == []


@pytest.mark.parametrize("code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_duplicate_report_exact_code_excludes_pair_of_excluded_code_signs(code: str) -> None:
    """Exact-code variant: a mount with 2 signs of an excluded code produces no results."""
    analyzer = _make_stub_with_two_signs(code)
    report = analyzer._get_duplicate_signs_on_same_mount(exact_code_match=True)
    assert report["results"] == []


@pytest.mark.parametrize("code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_duplicate_report_includes_three_excluded_code_signs(code: str) -> None:
    """Three signs with excluded code on same mount ARE reported (count > 2)."""
    mount = _make_mount("M-1")
    signs = [_make_sign(f"S-{i}", "M-1", code) for i in range(3)]
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={code: "dt-excluded"},
    )
    report = analyzer._get_duplicate_signs_on_same_mount(exact_code_match=False)
    assert len(report["results"]) == 1
    assert report["results"][0]["mount_source_id"] == "M-1"
    assert len(report["results"][0]["duplicate_signs"]) == 3


def test_duplicate_report_includes_non_excluded_code_pair() -> None:
    """Two signs with a non-excluded code on the same mount ARE reported."""
    code = "A1"
    mount = _make_mount("M-1")
    signs = [_make_sign(f"S-{i}", "M-1", code) for i in range(2)]
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={code: "dt-a1"},
    )
    report = analyzer._get_duplicate_signs_on_same_mount(exact_code_match=False)
    assert len(report["results"]) == 1
    assert report["results"][0]["mount_source_id"] == "M-1"


def test_duplicate_report_skips_removed_mount() -> None:
    """Signs on a Removed mount are never reported as duplicates."""
    code = "A1"
    mount = _make_mount("M-1", status="Removed")
    signs = [_make_sign(f"S-{i}", "M-1", code) for i in range(2)]
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={code: "dt-a1"},
    )
    report = analyzer._get_duplicate_signs_on_same_mount()
    assert report["results"] == []


def test_duplicate_report_skips_removed_signs() -> None:
    """Removed signs are not counted toward the duplicate threshold."""
    code = "A1"
    mount = _make_mount("M-1")
    signs = [
        _make_sign("S-1", "M-1", code, status="New"),
        _make_sign("S-2", "M-1", code, status="Removed"),
    ]
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={code: "dt-a1"},
    )
    report = analyzer._get_duplicate_signs_on_same_mount()
    assert report["results"] == []


def test_duplicate_report_correct_report_type_by_device_type() -> None:
    """_get_duplicate_signs_on_same_mount_by_device_type returns the correct REPORT_TYPE."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_mount_id={})
    report = analyzer._get_duplicate_signs_on_same_mount_by_device_type()
    assert report["REPORT_TYPE"] == "DUPLICATE SIGNS ON SAME MOUNT"


def test_duplicate_report_correct_report_type_exact_code() -> None:
    """_get_duplicate_signs_on_same_mount_exact_code returns the correct REPORT_TYPE."""
    analyzer = _StubAnalyzer(mounts_by_id={}, signs_by_mount_id={})
    report = analyzer._get_duplicate_signs_on_same_mount_exact_code()
    assert report["REPORT_TYPE"] == "DUPLICATE SIGNS ON SAME MOUNT (EXACT CODE)"


@pytest.mark.parametrize("excluded_code", sorted(DUPLICATE_PAIR_EXCLUDED_CODES))
def test_duplicate_report_mixed_excluded_and_non_excluded_codes_on_same_mount(excluded_code: str) -> None:
    """Only the non-excluded code pair is reported when both types are present on a mount."""
    normal_code = "B2"
    mount = _make_mount("M-1")
    signs = [
        _make_sign("S-excl-1", "M-1", excluded_code),
        _make_sign("S-excl-2", "M-1", excluded_code),
        _make_sign("S-norm-1", "M-1", normal_code),
        _make_sign("S-norm-2", "M-1", normal_code),
    ]
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": signs},
        code_to_device_type_id={excluded_code: "dt-excl", normal_code: "dt-norm"},
    )
    report = analyzer._get_duplicate_signs_on_same_mount(exact_code_match=True)
    assert len(report["results"]) == 1
    reported_ids = {s.split(" | ")[0] for s in report["results"][0]["duplicate_signs"]}
    assert reported_ids == {"S-norm-1", "S-norm-2"}
