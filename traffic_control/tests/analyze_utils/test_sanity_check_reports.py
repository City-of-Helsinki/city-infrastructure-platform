"""Tests for sanity-check report methods in ReportsMixin.

Covers:
- _get_main_signs_with_parent_report
- _get_signposts_that_are_both_parent_and_child_report
- _get_signless_additional_signs
- _get_mounts_without_any_signs_report
- _get_mounts_with_removed_signs_report
"""

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2
from traffic_control.analyze_utils.traffic_sign_data_v2_reports import ReportsMixin

# ==================== Helpers ====================


def _make_sign(
    sign_id: str,
    code: str = "A1",
    status: str = "New",
    parent_sign_id: str = "",
    mount_id: str = "M-1",
    ssurl: str = "",
) -> dict:
    """Build a minimal main-sign CSV row dict.

    Args:
        sign_id (str): Source ID of the sign.
        code (str): Device type code.
        status (str): Status value.
        parent_sign_id (str): Parent sign source ID (lisäkilven_päämerkin_id).
        mount_id (str): Mount source ID.
        ssurl (str): Attachment URL.

    Returns:
        dict: Minimal sign CSV row dict.
    """
    return {
        CSVHeadersV2.id: sign_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.status: status,
        CSVHeadersV2.parent_sign_id: parent_sign_id,
        CSVHeadersV2.mount_id: mount_id,
        CSVHeadersV2.attachment_url: ssurl,
    }


def _make_additional_sign(
    sign_id: str,
    code: str = "H1",
    status: str = "New",
    parent_sign_id: str = "",
    mount_id: str = "M-1",
    ssurl: str = "",
) -> dict:
    """Build a minimal additional-sign CSV row dict.

    Args:
        sign_id (str): Source ID of the additional sign.
        code (str): Device type code.
        status (str): Status value.
        parent_sign_id (str): Parent sign source ID (lisäkilven_päämerkin_id).
        mount_id (str): Mount source ID.
        ssurl (str): Attachment URL.

    Returns:
        dict: Minimal additional-sign CSV row dict.
    """
    return {
        CSVHeadersV2.id: sign_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.status: status,
        CSVHeadersV2.parent_sign_id: parent_sign_id,
        CSVHeadersV2.mount_id: mount_id,
        CSVHeadersV2.attachment_url: ssurl,
    }


def _make_signpost(
    sign_id: str,
    code: str = "F3",
    status: str = "New",
    parent_sign_id: str = "",
    mount_id: str = "M-1",
    ssurl: str = "",
) -> dict:
    """Build a minimal signpost CSV row dict.

    Args:
        sign_id (str): Source ID of the signpost.
        code (str): Device type code.
        status (str): Status value.
        parent_sign_id (str): Parent sign source ID.
        mount_id (str): Mount source ID.
        ssurl (str): Attachment URL.

    Returns:
        dict: Minimal signpost CSV row dict.
    """
    return {
        CSVHeadersV2.id: sign_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.status: status,
        CSVHeadersV2.parent_sign_id: parent_sign_id,
        CSVHeadersV2.mount_id: mount_id,
        CSVHeadersV2.attachment_url: ssurl,
    }


def _make_mount(mount_id: str, status: str = "New", ssurl: str = "") -> dict:
    """Build a minimal mount CSV row dict.

    Args:
        mount_id (str): Source ID of the mount.
        status (str): Status value.
        ssurl (str): Attachment URL.

    Returns:
        dict: Minimal mount CSV row dict.
    """
    return {
        CSVHeadersV2.id: mount_id,
        CSVHeadersV2.status: status,
        CSVHeadersV2.attachment_url: ssurl,
        CSVHeadersV2.mount_type: "pole",
        CSVHeadersV2.coord_x: "25496000",
        CSVHeadersV2.coord_y: "6672000",
        CSVHeadersV2.coord_z: "0",
    }


# ==================== Stubs ====================


class _StubAnalyzer(ReportsMixin):
    """Minimal stub satisfying ReportsMixin attribute requirements for sanity-check reports."""

    def __init__(
        self,
        signs_by_id: dict | None = None,
        additional_signs_by_id: dict | None = None,
        signposts_by_id: dict | None = None,
        mounts_by_id: dict | None = None,
        signs_by_mount_id: dict | None = None,
        additional_signs_by_mount_id: dict | None = None,
        signposts_by_mount_id: dict | None = None,
        signs_by_status: dict | None = None,
        additional_signs_by_status: dict | None = None,
        additional_sign_reals_by_source_id: dict | None = None,
    ) -> None:
        self.signs_by_id = signs_by_id or {}
        self.additional_signs_by_id = additional_signs_by_id or {}
        self.signposts_by_id = signposts_by_id or {}
        self.mounts_by_id = mounts_by_id or {}
        self.signs_by_mount_id = signs_by_mount_id or {}
        self.additional_signs_by_mount_id = additional_signs_by_mount_id or {}
        self.signposts_by_mount_id = signposts_by_mount_id or {}
        self.signs_by_status = signs_by_status or {"Removed": [], "New": []}
        self.additional_signs_by_status = additional_signs_by_status or {"Removed": [], "New": []}
        self.additional_sign_reals_by_source_id = additional_sign_reals_by_source_id or {}

    def _georeferenced_point_from_csv_row(self, row: dict):  # type: ignore[override]
        """Stub: return a fixed point."""
        from django.contrib.gis.geos import Point

        return Point(25496000, 6672000, 0, srid=3879)


# ==================== _get_main_signs_with_parent_report ====================


def test_main_signs_with_parent_report_type() -> None:
    """Report has the correct REPORT_TYPE value."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_main_signs_with_parent_report()
    assert report["REPORT_TYPE"] == "MAIN SIGNS WITH PARENT"


def test_main_signs_with_parent_empty_when_no_parents() -> None:
    """No results when no main signs have a parent_sign_id set."""
    sign = _make_sign("S-1", parent_sign_id="")
    analyzer = _StubAnalyzer(signs_by_id={"S-1": sign})
    report = analyzer._get_main_signs_with_parent_report()
    assert report["results"] == []


def test_main_signs_with_parent_detects_parent_is_additional_sign() -> None:
    """Parent resolved as additional_sign when parent_sign_id exists in additional_signs_by_id."""
    additional = _make_additional_sign("A-1", code="H9")
    sign = _make_sign("S-1", code="A1", parent_sign_id="A-1")
    analyzer = _StubAnalyzer(
        signs_by_id={"S-1": sign},
        additional_signs_by_id={"A-1": additional},
    )
    report = analyzer._get_main_signs_with_parent_report()
    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["sign_source_id"] == "S-1"
    assert result["parent_source_id"] == "A-1"
    assert result["parent_type"] == "additional_sign"
    assert result["parent_device_code"] == "H9"


def test_main_signs_with_parent_detects_parent_is_main_sign() -> None:
    """Parent resolved as main_sign when parent_sign_id exists in signs_by_id.

    This models the erroneous-but-real scenario described in the issue where
    the ``lisäkilven_päämerkin_id`` field on a main sign points to another main sign.
    """
    parent = _make_sign("S-parent", code="B3")
    child = _make_sign("S-child", code="A1", parent_sign_id="S-parent")
    analyzer = _StubAnalyzer(
        signs_by_id={"S-parent": parent, "S-child": child},
    )
    report = analyzer._get_main_signs_with_parent_report()
    # Only S-child has a non-empty parent_sign_id
    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["sign_source_id"] == "S-child"
    assert result["parent_source_id"] == "S-parent"
    assert result["parent_type"] == "main_sign"
    assert result["parent_device_code"] == "B3"


def test_main_signs_with_parent_detects_parent_not_found_in_csv() -> None:
    """Parent type is 'not_found_in_csv' when parent_sign_id is set but not in any collection."""
    sign = _make_sign("S-1", parent_sign_id="GHOST-99")
    analyzer = _StubAnalyzer(signs_by_id={"S-1": sign})
    report = analyzer._get_main_signs_with_parent_report()
    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["parent_type"] == "not_found_in_csv"
    assert result["parent_device_code"] is None
    assert result["parent_status"] is None


def test_main_signs_with_parent_result_includes_expected_fields() -> None:
    """Each result entry exposes all expected keys."""
    additional = _make_additional_sign("A-1", code="H9", status="Unchanged")
    sign = _make_sign("S-1", code="A1", status="New", parent_sign_id="A-1")
    analyzer = _StubAnalyzer(
        signs_by_id={"S-1": sign},
        additional_signs_by_id={"A-1": additional},
    )
    report = analyzer._get_main_signs_with_parent_report()
    result = report["results"][0]
    expected_keys = {
        "sign_source_id",
        "sign_device_code",
        "sign_status",
        "parent_source_id",
        "parent_device_code",
        "parent_type",
        "parent_status",
    }
    assert expected_keys.issubset(result.keys())


def test_main_signs_with_parent_prefers_additional_sign_over_main_sign() -> None:
    """When parent_sign_id matches both collections, additional_sign takes precedence."""
    shared_id = "SHARED-1"
    additional = _make_additional_sign(shared_id, code="H9")
    other_sign = _make_sign(shared_id, code="B3")
    child = _make_sign("S-child", parent_sign_id=shared_id)
    analyzer = _StubAnalyzer(
        signs_by_id={"S-child": child, shared_id: other_sign},
        additional_signs_by_id={shared_id: additional},
    )
    report = analyzer._get_main_signs_with_parent_report()
    result = report["results"][0]
    assert result["parent_type"] == "additional_sign"


# ==================== _get_signposts_that_are_both_parent_and_child_report ====================


def test_signposts_both_parent_and_child_report_type() -> None:
    """Report has the correct REPORT_TYPE value."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    assert report["REPORT_TYPE"] == "SIGNPOSTS THAT ARE BOTH PARENT AND CHILD"


def test_signposts_both_parent_and_child_empty_when_no_signposts() -> None:
    """No results when there are no signposts."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    assert report["results"] == []


def test_signposts_both_parent_and_child_empty_when_no_chain() -> None:
    """No results when no signpost is both a parent and a child."""
    sp_a = _make_signpost("SP-A")
    sp_b = _make_signpost("SP-B", parent_sign_id="SP-A")
    analyzer = _StubAnalyzer(signposts_by_id={"SP-A": sp_a, "SP-B": sp_b})
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    # SP-A is a parent but not a child; SP-B is a child but not a parent
    assert report["results"] == []


def test_signposts_both_parent_and_child_detects_middle_node() -> None:
    """Middle node in a chain (child of one, parent of another) is reported.

    SP-A -> SP-B -> SP-C: SP-B is both child of SP-A and parent of SP-C.
    """
    sp_a = _make_signpost("SP-A")
    sp_b = _make_signpost("SP-B", parent_sign_id="SP-A")
    sp_c = _make_signpost("SP-C", parent_sign_id="SP-B")
    signposts = {"SP-A": sp_a, "SP-B": sp_b, "SP-C": sp_c}
    analyzer = _StubAnalyzer(signposts_by_id=signposts)
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    assert len(report["results"]) == 1
    assert report["results"][0]["signpost_source_id"] == "SP-B"
    assert report["results"][0]["parent_signpost_source_id"] == "SP-A"


def test_signposts_both_parent_and_child_result_includes_expected_fields() -> None:
    """Each result entry exposes all expected keys."""
    sp_a = _make_signpost("SP-A", code="F3", status="New", ssurl="http://a")
    sp_b = _make_signpost("SP-B", code="F4", status="Unchanged", parent_sign_id="SP-A", ssurl="http://b")
    sp_c = _make_signpost("SP-C", parent_sign_id="SP-B")
    signposts = {"SP-A": sp_a, "SP-B": sp_b, "SP-C": sp_c}
    analyzer = _StubAnalyzer(signposts_by_id=signposts)
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    result = report["results"][0]
    expected_keys = {
        "signpost_source_id",
        "devicetypecode",
        "status",
        "internal_status",
        "parent_signpost_source_id",
        "parent_devicetypecode",
        "parent_status",
        "csv_ssurl",
        "parent_csv_ssurl",
    }
    assert expected_keys.issubset(result.keys())


def test_signposts_both_parent_and_child_ignores_external_parent_ids() -> None:
    """parent_sign_id pointing outside signposts_by_id does not create a child relationship."""
    sp_a = _make_signpost("SP-A", parent_sign_id="EXTERNAL-99")
    sp_b = _make_signpost("SP-B", parent_sign_id="SP-A")
    signposts = {"SP-A": sp_a, "SP-B": sp_b}
    analyzer = _StubAnalyzer(signposts_by_id=signposts)
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    # SP-A's parent is external so SP-A is not a child; SP-B is only a child
    assert report["results"] == []


def test_signposts_both_parent_and_child_multiple_children() -> None:
    """A signpost that is both a parent of multiple and a child is reported once."""
    sp_a = _make_signpost("SP-A")
    sp_b = _make_signpost("SP-B", parent_sign_id="SP-A")
    sp_c = _make_signpost("SP-C", parent_sign_id="SP-B")
    sp_d = _make_signpost("SP-D", parent_sign_id="SP-B")
    signposts = {"SP-A": sp_a, "SP-B": sp_b, "SP-C": sp_c, "SP-D": sp_d}
    analyzer = _StubAnalyzer(signposts_by_id=signposts)
    report = analyzer._get_signposts_that_are_both_parent_and_child_report()
    reported_ids = [r["signpost_source_id"] for r in report["results"]]
    assert reported_ids.count("SP-B") == 1


# ==================== _get_signless_additional_signs ====================


def test_signless_additional_signs_report_type() -> None:
    """Report has the correct REPORT_TYPE value."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_signless_additional_signs()
    assert report["REPORT_TYPE"] == "SIGNLESS ADDITIONAL SIGNS"


def test_signless_additional_signs_empty_when_all_have_parent() -> None:
    """No results when every additional sign has a parent_sign_id set."""
    add_sign = _make_additional_sign("A-1", parent_sign_id="S-1")
    analyzer = _StubAnalyzer(additional_signs_by_id={"A-1": add_sign})
    report = analyzer._get_signless_additional_signs()
    assert report["results"] == []


def test_signless_additional_signs_reports_sign_without_parent() -> None:
    """Additional sign with empty parent_sign_id is included in results."""
    add_sign = _make_additional_sign("A-1", code="H5", status="New", parent_sign_id="")
    analyzer = _StubAnalyzer(additional_signs_by_id={"A-1": add_sign})
    report = analyzer._get_signless_additional_signs()
    assert len(report["results"]) == 1
    result = report["results"][0]
    assert result["additional_sign_source_id"] == "A-1"
    assert result["new_device_code"] == "H5"
    assert result["status"] == "New"


def test_signless_additional_signs_result_includes_expected_fields() -> None:
    """Each result entry has the expected keys."""
    add_sign = _make_additional_sign("A-1", parent_sign_id="")
    analyzer = _StubAnalyzer(additional_signs_by_id={"A-1": add_sign})
    report = analyzer._get_signless_additional_signs()
    result = report["results"][0]
    expected_keys = {
        "additional_sign_source_id",
        "old_device_code",
        "new_device_code",
        "status",
        "internal_status",
        "csv_ssurl",
    }
    assert expected_keys.issubset(result.keys())


def test_signless_additional_signs_mixed_results() -> None:
    """Only signs without parent_sign_id are reported; signs with parent_sign_id are omitted."""
    with_parent = _make_additional_sign("A-1", parent_sign_id="S-1")
    without_parent = _make_additional_sign("A-2", parent_sign_id="")
    analyzer = _StubAnalyzer(
        additional_signs_by_id={"A-1": with_parent, "A-2": without_parent},
    )
    report = analyzer._get_signless_additional_signs()
    assert len(report["results"]) == 1
    assert report["results"][0]["additional_sign_source_id"] == "A-2"


# ==================== _get_mounts_without_any_signs_report ====================


def test_mounts_without_any_signs_report_type() -> None:
    """Report has the correct REPORT_TYPE value."""
    analyzer = _StubAnalyzer()
    report = analyzer._get_mounts_without_any_signs_report()
    assert report["REPORT_TYPE"] == "MOUNTS WITHOUT ANY SIGNS"


def test_mounts_without_any_signs_reports_unattached_mount() -> None:
    """A mount with no signs, additional signs or signposts is included."""
    mount = _make_mount("M-1")
    analyzer = _StubAnalyzer(mounts_by_id={"M-1": mount})
    report = analyzer._get_mounts_without_any_signs_report()
    assert len(report["results"]) == 1
    assert report["results"][0]["mount_source_id"] == "M-1"


def test_mounts_without_any_signs_excludes_mount_with_sign() -> None:
    """A mount referenced by at least one sign is excluded from the report."""
    mount = _make_mount("M-1")
    analyzer = _StubAnalyzer(
        mounts_by_id={"M-1": mount},
        signs_by_mount_id={"M-1": [_make_sign("S-1")]},
    )
    report = analyzer._get_mounts_without_any_signs_report()
    assert report["results"] == []


@pytest.mark.parametrize(
    "collection_attr", ["signs_by_mount_id", "additional_signs_by_mount_id", "signposts_by_mount_id"]
)
def test_mounts_without_any_signs_excludes_mount_with_any_object_type(collection_attr: str) -> None:
    """A mount with any attached object type (sign, additional sign, signpost) is excluded."""
    mount = _make_mount("M-1")
    kwargs: dict = {"mounts_by_id": {"M-1": mount}, collection_attr: {"M-1": [_make_sign("OBJ-1")]}}
    analyzer = _StubAnalyzer(**kwargs)
    report = analyzer._get_mounts_without_any_signs_report()
    assert report["results"] == []
