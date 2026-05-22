"""Tests for TrafficSignAnalyzerV2 and analyze_traffic_sign_data_v2 management command."""
import csv
import os
from pathlib import Path

import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data_v2 import TrafficSignAnalyzerV2
from traffic_control.analyze_utils.traffic_sign_data_v2_code_transform import CodeTransformMixin
from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CSVHeadersV2
from traffic_control.models import MountType, TrafficControlDeviceType
from traffic_control.tests.factories import SignpostRealFactory, TrafficSignRealFactory

BASE_PATH = os.path.dirname(__file__)
TEST_FILES_DIR = os.path.join(BASE_PATH, "../../test_datas/traffic_sign_import_v2")


_MOUNT_CSV_HEADER: list[str] = [
    "OBJECTID",
    "id",
    "x",
    "y",
    "z",
    "stdx",
    "stdy",
    "stdz",
    "status",
    "tallennusajankohta",
    "ssurl",
]
_SIGN_CSV_HEADER: list[str] = [
    "OBJECTID",
    "id",
    "x",
    "y",
    "z",
    "stdx",
    "stdy",
    "stdz",
    "kiinnityskohta_id",
    "status",
    "merkkikoodi",
    "teksti",
    "teksti_suomeksi",
    "teksti_ruotsiksi",
    "kiinnitys",
    "numerokoodi",
    "merkin_ehto",
    "taustaväri",
    "atsimuutti",
    "lisäkilven_päämerkin_id",
    "tallennusajankohta",
    "korkeus",
    "ssurl",
]
_COORDS = ["25497188.0", "6673461.0", "8.0", "0.01", "0.01", "0.01"]
_TS = "2023-08-15T12:00:00+00:00"


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def _mount_row(obj_id: str, status: str = "New", ssurl: str = "") -> list[str]:
    """Build a mount CSV row as a list of field values.

    Args:
        obj_id (str): Object identifier.
        status (str): Mount status string.
        ssurl (str): Source system URL.

    Returns:
        list[str]: Field values for one mount row.
    """
    return ["1", obj_id] + _COORDS + [status, _TS, ssurl]


def _sign_row(
    obj_id: str,
    mount_id: str,
    status: str,
    code: str,
    color: str = "",
    ssurl: str = "",
    numero: str = "",
    atsimuutti: str = "",
    parent_id: str = "",
) -> list[str]:
    """Build a sign CSV row as a list of field values.

    Args:
        obj_id (str): Object identifier.
        mount_id (str): Related mount identifier.
        status (str): Sign status string.
        code (str): Sign code.
        color (str): Background colour value.
        ssurl (str): Source system URL.
        numero (str): Numeric code.
        atsimuutti (str): Azimuth value.
        parent_id (str): Parent sign identifier for additional signs.

    Returns:
        list[str]: Field values for one sign row.
    """
    # Header columns 11-23:
    # code(11), teksti(12), suomeksi(13), ruotsiksi(14), kiinnitys(15),
    # numero(16), merkin_ehto(17), color/taustaväri(18), atsimuutti(19),
    # parent_id(20), ts(21), korkeus(22), ssurl(23)
    return (
        ["1", obj_id]
        + _COORDS
        + [mount_id, status, code, "", "", "", "", numero, "", color, atsimuutti, parent_id, _TS, "3.0", ssurl]
    )


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> str:
    """Write a minimal CSV file using csv.writer and return its path as a string.

    Args:
        path (Path): Directory to write the file into.
        header (list[str]): Column name fields for the header row.
        rows (list[list[str]]): Data rows as lists of field values.

    Returns:
        str: Absolute path of the written file.
    """
    file_path = path / f"test_{id(rows)}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    return str(file_path)


def _make_analyzer(tmp_path: Path, mount_rows: list[list[str]], sign_rows: list[list[str]]) -> TrafficSignAnalyzerV2:
    """Build a TrafficSignAnalyzerV2 from inline rows.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        mount_rows (list[list[str]]): Mount CSV data rows as field-value lists.
        sign_rows (list[list[str]]): Sign CSV data rows as field-value lists.

    Returns:
        TrafficSignAnalyzerV2: Configured analyzer instance.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows)
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, sign_rows)
    return TrafficSignAnalyzerV2(mf, sf, delimiter=",", output_dir=str(tmp_path))


def _create_db_entries():
    """Create necessary database entries for tests."""
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    for code in ["C39", "C40", "H24S", "H24", "645", "511", "5111", "5112", "E1", "E1_2"]:
        TrafficControlDeviceType.objects.get_or_create(code=code)


# ===========================================================================
# Pure-logic unit tests (no database)
# ===========================================================================


@pytest.mark.parametrize(
    "code,expected",
    [
        ("645", True),
        ("644", True),
        ("F21.1", True),
        ("F2.1", True),
        ("G4", True),
        ("G15", True),
        ("726", True),
        ("7xx", True),
        ("6xx", True),
        ("6", False),
        ("7", False),
        ("C39", False),
        ("H24S", False),
        ("833", False),
        ("", False),
    ],
)
def test_is_signpost(code: str, expected: bool) -> None:
    """_is_signpost classifies codes starting with 6/7/G/F (not exact 6 or 7).

    Args:
        code (str): Device type code to test.
        expected (bool): Expected classification result.
    """
    assert TrafficSignAnalyzerV2._is_signpost({CSVHeadersV2.code: code}) is expected


@pytest.mark.parametrize(
    "code,expected",
    [
        ("H24S", True),
        ("H1", True),
        ("8xx", True),
        ("833", True),
        ("C39", False),
        ("645", False),
        ("F21", False),
        ("G4", False),
        ("", False),
    ],
)
def test_is_additional_sign(code: str, expected: bool) -> None:
    """_is_additional_sign classifies codes starting with H or 8.

    Args:
        code (str): Device type code to test.
        expected (bool): Expected classification result.
    """
    assert bool(TrafficSignAnalyzerV2._is_additional_sign({CSVHeadersV2.code: code})) is expected


@pytest.mark.parametrize(
    "code,expected",
    [
        ("6", True),
        ("7", True),
        ("645", False),
        ("F21.1", False),
        ("G4", False),
        ("C39", False),
        ("7xx", False),
        ("6xx", False),
        ("", False),
    ],
)
def test_is_skippable_code(code: str, expected: bool) -> None:
    """_is_skippable_code returns True only for exact '6' or '7'.

    Args:
        code (str): Code to test.
        expected (bool): Expected result.
    """
    assert TrafficSignAnalyzerV2._is_skippable_code(code) is expected


@pytest.mark.parametrize(
    "timestamp_str,object_type,should_be_error",
    [
        ("2023/08/15 12:00:00+00", "mount", False),  # valid format for _get_sign_scanned_at
        ("not-a-timestamp", "traffic_sign", True),
        ("", "additional_sign", False),
        ("INVALID", "signpost", True),
    ],
)
def test_validate_timestamp(timestamp_str: str, object_type: str, should_be_error: bool) -> None:
    """_validate_timestamp returns an error dict for invalid timestamps, None otherwise.

    Args:
        timestamp_str (str): Timestamp string to validate.
        object_type (str): Object type label.
        should_be_error (bool): Whether an error dict should be returned.
    """
    obj = {CSVHeadersV2.scanned_at: timestamp_str, CSVHeadersV2.id: "test_id"}
    result = TrafficSignAnalyzerV2._validate_timestamp(obj, object_type)
    if should_be_error:
        assert result is not None
        assert result["object_type"] == object_type
        assert result["invalid_timestamp"] == timestamp_str
    else:
        assert result is None


@pytest.mark.parametrize(
    "object_type,expected_key",
    [
        ("mount", "mount_source_id"),
        ("traffic_sign", "sign_source_id"),
        ("additional_sign", "additional_sign_source_id"),
        ("signpost", "signpost_source_id"),
    ],
)
def test_validate_timestamp_id_key_per_object_type(object_type: str, expected_key: str) -> None:
    """_validate_timestamp uses the correct id key for each object type.

    Args:
        object_type (str): Object type label.
        expected_key (str): Expected key in the returned error dict.
    """
    obj = {CSVHeadersV2.scanned_at: "INVALID", CSVHeadersV2.mount_scanned_at: "INVALID", CSVHeadersV2.id: "the_id"}
    result = TrafficSignAnalyzerV2._validate_timestamp(obj, object_type)
    assert result is not None
    assert expected_key in result
    assert result[expected_key] == "the_id"


@pytest.mark.parametrize(
    "x,y,expected_none",
    [
        ("25497188.0", "6673461.0", False),
        ("invalid", "6673461.0", True),
        ("25497188.0", "invalid", True),
        ("", "6673461.0", True),
    ],
)
def test_point_from_csv_row(x: str, y: str, expected_none: bool) -> None:
    """_point_from_csv_row returns a Point for valid coords or None for invalid.

    Args:
        x (str): X-coordinate string.
        y (str): Y-coordinate string.
        expected_none (bool): Whether None is expected.
    """
    row = {CSVHeadersV2.coord_x: x, CSVHeadersV2.coord_y: y}
    result = TrafficSignAnalyzerV2._point_from_csv_row(row)
    if expected_none:
        assert result is None
    else:
        assert isinstance(result, Point)


def test_group_by_mount_id() -> None:
    """_group_by_mount_id groups sign dicts into lists keyed by mount_id."""
    signs = {
        "s1": {CSVHeadersV2.mount_id: "m1", CSVHeadersV2.id: "s1"},
        "s2": {CSVHeadersV2.mount_id: "m1", CSVHeadersV2.id: "s2"},
        "s3": {CSVHeadersV2.mount_id: "m2", CSVHeadersV2.id: "s3"},
    }
    result = TrafficSignAnalyzerV2._group_by_mount_id(signs)
    assert {r[CSVHeadersV2.id] for r in result["m1"]} == {"s1", "s2"}
    assert len(result["m2"]) == 1
    assert result["m2"][0][CSVHeadersV2.id] == "s3"


# ===========================================================================
# Color-based suffix tests
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,color,expected_new_code,expected_type,expected_color_value",
    [
        ("824", "", "824K", "color_based_default", "default_K"),
        ("825", "", "825K", "color_based_default", "default_K"),
        ("826", "", "826K", "color_based_default", "default_K"),
        ("828", "", "828K", "color_based_default", "default_K"),
        ("843", "", "843S", "color_based_default", "default_S"),
        ("824", "1", "824S", "color_based", "1"),
        ("824", "2", "824K", "color_based", "2"),
        ("843", "1", "843S", "color_based", "1"),
        ("843", "2", "843K", "color_based", "2"),
    ],
)
def test_color_based_suffix_replacement(
    tmp_path: Path,
    code: str,
    color: str,
    expected_new_code: str,
    expected_type: str,
    expected_color_value: str,
) -> None:
    """Color-based suffix transformations produce the correct new code and metadata.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Original device type code.
        color (str): Color field value (1, 2, or empty).
        expected_new_code (str): Code expected after transformation.
        expected_type (str): Expected replacement_type in the replacement record.
        expected_color_value (str): Expected color_value in the replacement record.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=expected_new_code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row(f"sign_{code}_{color or 'empty'}", "m1", "New", code, color=color)],
    )

    matches = [r for r in analyzer.code_replacements if r.get("replacement_type") == expected_type]
    assert len(matches) == 1
    assert matches[0]["old_code"] == code
    assert matches[0]["new_code"] == expected_new_code
    assert matches[0]["color_value"] == expected_color_value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,color,expected_reason",
    [
        ("814", "", "missing_color_field"),
        ("831", "X", "invalid_color_value"),
        ("833", "3", "invalid_color_value"),
    ],
)
def test_color_replacement_failure(tmp_path: Path, code: str, color: str, expected_reason: str) -> None:
    """Missing or invalid color fields produce replacement failure records.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code that requires a color suffix.
        color (str): Invalid or missing color value.
        expected_reason (str): Expected reason key in the failure record.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row(f"sign_fail_{code}", "m1", "New", code, color=color)],
    )

    failures = [f for f in analyzer.code_replacement_failures if f["reason"] == expected_reason]
    assert len(failures) >= 1
    assert failures[0]["code"] == code


# ===========================================================================
# Signpost classification
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,in_signposts,in_signs,in_additional",
    [
        ("645", True, False, False),
        ("F21.1", True, False, False),
        ("G4", True, False, False),
        ("726", True, False, False),
        ("C39", False, True, False),
        ("H24S", False, False, True),
        ("833", False, False, True),
    ],
)
def test_sign_classification(
    tmp_path: Path, code: str, in_signposts: bool, in_signs: bool, in_additional: bool
) -> None:
    """Signs are routed to the correct by-id dict based on their code prefix.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        in_signposts (bool): Should appear in signposts_by_id.
        in_signs (bool): Should appear in signs_by_id.
        in_additional (bool): Should appear in additional_signs_by_id.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(tmp_path, [_mount_row("m1")], [_sign_row("obj1", "m1", "New", code)])

    assert ("obj1" in analyzer.signposts_by_id) is in_signposts
    assert ("obj1" in analyzer.signs_by_id) is in_signs
    assert ("obj1" in analyzer.additional_signs_by_id) is in_additional


@pytest.mark.django_db
def test_skippable_exact_6_and_7_are_filtered(tmp_path: Path) -> None:
    """Rows with code exactly '6' or '7' are removed from all sign dicts.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("skip6", "m1", "New", "6"), _sign_row("skip7", "m1", "New", "7")],
    )
    for sid in ("skip6", "skip7"):
        assert sid not in analyzer.signposts_by_id
        assert sid not in analyzer.signs_by_id
        assert sid not in analyzer.additional_signs_by_id


# ===========================================================================
# Non-existing mounts reports
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,report_type,id_key,ssurl_key",
    [
        ("C39", "NON EXISTING MOUNTS FOR SIGNS", "sign_source_id", "csv_ssurl"),
        ("H24S", "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS", "additional_sign_source_id", "additional_sign_ssurl"),
        ("645", "NON EXISTING MOUNTS FOR SIGNPOSTS", "signpost_source_id", "csv_ssurl"),
    ],
)
def test_non_existing_mounts_reports(tmp_path: Path, code: str, report_type: str, id_key: str, ssurl_key: str) -> None:
    """Non-existing-mounts reports identify signs referencing absent mounts.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        report_type (str): Expected REPORT_TYPE string.
        id_key (str): Expected source_id key in result dicts.
        ssurl_key (str): Expected ssurl key name in result dicts.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("real_mount")],
        [_sign_row("obj1", "missing_mount", "New", code, ssurl="https://example.com/img")],
    )
    reports = analyzer.analyze()
    report = next(r for r in reports if r["REPORT_TYPE"] == report_type)
    result = next((r for r in report["results"] if r.get(id_key) == "obj1"), None)
    assert result is not None
    assert ssurl_key in result
    assert result[ssurl_key] == "https://example.com/img"
    assert "mount_ssurl" in result


# ===========================================================================
# Remove records report
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,expected_id_key",
    [
        ("C39", "sign_source_id"),
        ("H24S", "additional_sign_source_id"),
        ("645", "signpost_source_id"),
    ],
)
def test_remove_records_includes_all_types(tmp_path: Path, code: str, expected_id_key: str) -> None:
    """Remove-records report includes entries for signs, additional signs, and signposts.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        expected_id_key (str): Expected source_id key in result dicts.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("removed_obj", "m1", "Removed", code)],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "REMOVE RECORDS")
    ids = [r.get(expected_id_key) for r in report["results"]]
    assert "removed_obj" in ids


# ===========================================================================
# Status mismatch report
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "csv_status,db_code,csv_code,expected_reason_fragment",
    [
        ("New", "C39", "C39", "Marked as New but already exists"),
        ("Unchanged", None, "C39", "Marked as Unchanged but not found"),
        ("Unchanged", "C40", "C39", "Marked as Unchanged but device type code differs"),
        ("Changed", None, "C39", "Marked as Changed but not found"),
        ("Changed", "C39", "C39", "Marked as Changed but device type code matches"),
        ("Removed", None, "C39", "Marked as Removed but not found"),
    ],
)
def test_status_mismatch_reason(
    tmp_path: Path,
    csv_status: str,
    db_code: str | None,
    csv_code: str,
    expected_reason_fragment: str,
) -> None:
    """Status mismatch report contains the correct mismatch reason string.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        csv_status (str): CSV status value for the sign row.
        db_code (str | None): Device type code in DB (None = sign not in DB).
        csv_code (str): Device type code in the CSV row.
        expected_reason_fragment (str): Substring expected in mismatch_reason.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")
    TrafficControlDeviceType.objects.get_or_create(code="C40")

    if db_code is not None:
        dt, _ = TrafficControlDeviceType.objects.get_or_create(code=db_code)
        TrafficSignRealFactory(source_id="sign_mismatch", source_name="StreetScan", device_type=dt)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("sign_mismatch", "m1", csv_status, csv_code)],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "STATUS AND INTERNAL_STATUS MISMATCH")
    results = [r for r in report["results"] if r.get("source_id") == "sign_mismatch"]
    assert len(results) == 1
    assert expected_reason_fragment in results[0]["mismatch_reason"]


# ===========================================================================
# Missing from database reports
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,report_type,id_key,expect_ssurl",
    [
        ("C39", "MISSING TRAFFIC SIGNS FROM DATABASE", "sign_source_id", True),
        ("H24S", "MISSING ADDITIONAL SIGNS FROM DATABASE", "additional_sign_source_id", False),
        ("645", "MISSING SIGNPOSTS FROM DATABASE", "signpost_source_id", True),
    ],
)
def test_missing_from_database_report(
    tmp_path: Path, code: str, report_type: str, id_key: str, expect_ssurl: bool
) -> None:
    """Missing-from-database reports identify non-New objects absent from the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        report_type (str): Expected REPORT_TYPE string.
        id_key (str): Expected source_id key in result dicts.
        expect_ssurl (bool): Whether csv_ssurl should be present.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("not_in_db", "m1", "Unchanged", code, ssurl="https://x.com")],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == report_type)
    result = next((r for r in report["results"] if r.get(id_key) == "not_in_db"), None)
    assert result is not None
    assert result["status"] == "Unchanged"
    assert ("csv_ssurl" in result) is expect_ssurl


# ===========================================================================
# Found in database reports
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,use_signpost_factory,report_type",
    [
        ("C39", False, "TRAFFIC SIGNS FOUND IN DATABASE"),
        ("645", True, "SIGNPOSTS FOUND IN DATABASE"),
    ],
)
def test_found_in_database_report(tmp_path: Path, code: str, use_signpost_factory: bool, report_type: str) -> None:
    """Found-in-database reports list objects present in both CSV and DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        use_signpost_factory (bool): True to create a SignpostReal, False for TrafficSignReal.
        report_type (str): Expected REPORT_TYPE string.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    device_type, _ = TrafficControlDeviceType.objects.get_or_create(code=code)

    if use_signpost_factory:
        SignpostRealFactory(source_id="in_db_obj", source_name="StreetScan", device_type=device_type)
    else:
        TrafficSignRealFactory(source_id="in_db_obj", source_name="StreetScan", device_type=device_type)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("in_db_obj", "m1", "Unchanged", code)],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == report_type)
    assert "in_db_obj" in [r.get("source_id") for r in report["results"]]


# ===========================================================================
# Signpost-specific report types
# ===========================================================================


@pytest.mark.django_db
def test_analyze_includes_signpost_report_types(tmp_path: Path) -> None:
    """analyze() produces all four signpost-specific report types.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    _create_db_entries()
    TrafficControlDeviceType.objects.get_or_create(code="645")
    analyzer = _make_analyzer(tmp_path, [_mount_row("m1")], [_sign_row("sp1", "m1", "New", "645")])
    report_types = {r["REPORT_TYPE"] for r in analyzer.analyze()}

    for rt in [
        "NON EXISTING MOUNTS FOR SIGNPOSTS",
        "MISSING SIGNPOSTS FROM DATABASE",
        "SIGNPOSTS FOUND IN DATABASE",
        "SIGNPOST CSV TO DB LOCATION DISTANCE",
    ]:
        assert rt in report_types, f"Missing report type: {rt}"


# ===========================================================================
# Timestamp format validation
# ===========================================================================


@pytest.mark.django_db
def test_timestamp_format_validation_report(tmp_path: Path) -> None:
    """Invalid timestamps appear in the timestamp format errors report.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")

    mount_rows = [["1", "m1", "25497188.0", "6673461.0", "8.0", "0.01", "0.01", "0.01", "New", "NOT_A_DATE", ""]]
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows)
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [_sign_row("s1", "m1", "New", "C39")])
    analyzer = TrafficSignAnalyzerV2(mf, sf, delimiter=",", output_dir=str(tmp_path))
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "TIMESTAMP FORMAT ERRORS")
    assert any(r.get("mount_source_id") == "m1" for r in report["results"])


# ===========================================================================
# Invalid device type codes
# ===========================================================================


@pytest.mark.django_db
def test_invalid_device_type_codes_report(tmp_path: Path) -> None:
    """Unknown device type codes appear in the invalid-codes report.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    # UNKNOWN_XYZ not created in DB on purpose
    analyzer = _make_analyzer(tmp_path, [_mount_row("m1")], [_sign_row("s1", "m1", "New", "UNKNOWN_XYZ")])
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "INVALID DEVICE TYPE CODES")
    assert "UNKNOWN_XYZ" in [r.get("invalid_code") for r in report["results"]]


# ===========================================================================
# Distance calculations
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "code,dict_attr",
    [
        ("C39", "signs_by_id"),
        ("645", "signposts_by_id"),
        ("H24S", "additional_signs_by_id"),
    ],
)
def test_distance_to_mount_calculated(tmp_path: Path, code: str, dict_attr: str) -> None:
    """Signs with a matching mount get a non-None positive distance_to_mount.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        code (str): Device type code.
        dict_attr (str): Analyzer attribute name holding the relevant dict.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    mount_rows = [
        ["1", "m1", "25497200.0", "6673461.0", "8.0", "0.01", "0.01", "0.01", "New", "2023-08-15T12:00:00+00:00", ""]
    ]
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows)
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [_sign_row("obj1", "m1", "New", code)])
    analyzer = TrafficSignAnalyzerV2(mf, sf, delimiter=",", output_dir=str(tmp_path))

    d = getattr(analyzer, dict_attr)["obj1"]["distance_to_mount"]
    assert d is not None
    assert d > 0


@pytest.mark.django_db
def test_distance_to_mount_none_when_mount_missing(tmp_path: Path) -> None:
    """Signs referencing a non-existent mount get distance_to_mount = None.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")
    analyzer = _make_analyzer(tmp_path, [_mount_row("real_mount")], [_sign_row("s1", "no_such_mount", "New", "C39")])
    assert analyzer.signs_by_id["s1"]["distance_to_mount"] is None


# ===========================================================================
# csv_ssurl fields in reports
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "report_type,id_key,ssurl_key",
    [
        ("NON EXISTING MOUNTS FOR SIGNS", "sign_source_id", "csv_ssurl"),
        ("NON EXISTING MOUNTS FOR ADDITIONAL SIGNS", "additional_sign_source_id", "additional_sign_ssurl"),
        ("NON EXISTING MOUNTS FOR SIGNPOSTS", "signpost_source_id", "csv_ssurl"),
    ],
)
def test_non_existing_mounts_ssurl_fields(tmp_path: Path, report_type: str, id_key: str, ssurl_key: str) -> None:
    """Non-existing-mounts reports include both an ssurl and mount_ssurl field.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        report_type (str): Expected REPORT_TYPE string.
        id_key (str): Expected source_id key in result dicts.
        ssurl_key (str): Expected ssurl key name in result dicts.
    """
    code_map = {
        "sign_source_id": "C39",
        "additional_sign_source_id": "H24S",
        "signpost_source_id": "645",
    }
    code = code_map[id_key]
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code=code)

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("real_mount")],
        [_sign_row("obj1", "missing_mount", "New", code, ssurl="https://img.example")],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == report_type)
    result = next(r for r in report["results"] if r.get(id_key) == "obj1")
    assert result[ssurl_key] == "https://img.example"
    assert "mount_ssurl" in result


# ===========================================================================
# Full integration: existing test suite
# ===========================================================================


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_basic(tmp_path):
    """TrafficSignAnalyzerV2 loads CSV files and segregates by status."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    assert len(analyzer.mounts_by_id) > 0
    assert len(analyzer.signs_by_id) > 0
    assert len(analyzer.additional_signs_by_id) > 0
    for status in ("New", "Unchanged", "Changed", "Removed", "invalid"):
        assert status in analyzer.mounts_by_status or status in analyzer.signs_by_status


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_reports(tmp_path):
    """TrafficSignAnalyzerV2.analyze() generates all expected report types."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    report_types = {r["REPORT_TYPE"] for r in analyzer.analyze()}
    for rt in [
        "NON EXISTING MOUNTS FOR SIGNS",
        "NON EXISTING MOUNTS FOR ADDITIONAL SIGNS",
        "NON EXISTING MOUNTS FOR SIGNPOSTS",
        "MOUNT DISTANCES",
        "SIGN DISTANCES",
        "ADDITIONAL SIGN DISTANCES",
        "MOUNTLESS SIGNS",
        "MOUNTLESS ADDITIONAL SIGNS",
        "SIGNLESS ADDITIONAL SIGNS",
        "STATUS DISTRIBUTION",
        "INVALID STATUS VALUES",
        "CHANGED RECORDS",
        "UNCHANGED RECORDS",
        "REMOVE RECORDS",
        "REMOVE WITH INVALID LOCATION",
        "TIMESTAMP FORMAT ERRORS",
        "INVALID DEVICE TYPE CODES",
        "MISSING MOUNTS FROM DATABASE",
        "MISSING TRAFFIC SIGNS FROM DATABASE",
        "MISSING ADDITIONAL SIGNS FROM DATABASE",
        "MISSING SIGNPOSTS FROM DATABASE",
        "DUPLICATE SIGNS ON SAME MOUNT",
        "DUPLICATE SIGNS ON SAME MOUNT (EXACT CODE)",
        "ADDED DOUBLE SIDED ZEBRA CROSSINGS",
        "MOUNTS FOUND IN DATABASE",
        "TRAFFIC SIGNS FOUND IN DATABASE",
        "ADDITIONAL SIGNS FOUND IN DATABASE",
        "SIGNPOSTS FOUND IN DATABASE",
        "MAIN SIGNS WITH PARENT",
        "MOUNTS WITH REMOVED SIGNS",
        "SIGNPOST CSV TO DB LOCATION DISTANCE",
    ]:
        assert rt in report_types, f"Missing report type: {rt}"


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_status_distribution(tmp_path):
    """Status distribution report results contain required fields."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    status_report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "STATUS DISTRIBUTION")
    assert len(status_report["results"]) > 0
    for result in status_report["results"]:
        for key in ("object_type", "status", "count", "percentage"):
            assert key in result


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_duplicate_detection(tmp_path):
    """Duplicate signs on same mount are detected correctly."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    dup_report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "DUPLICATE SIGNS ON SAME MOUNT")
    assert len(dup_report["results"]) > 0
    dup = dup_report["results"][0]
    assert "mount_source_id" in dup
    assert "mount_location" in dup
    assert isinstance(dup["duplicate_signs"], list)
    assert len(dup["duplicate_signs"]) >= 2


@pytest.mark.django_db
def test_traffic_sign_analyzer_v2_zebra_crossings(tmp_path):
    """Double-sided zebra crossings are detected correctly."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    zebra_report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ADDED DOUBLE SIDED ZEBRA CROSSINGS")
    assert len(zebra_report["results"]) > 0
    zebra = zebra_report["results"][0]
    assert len(zebra["sign_source_ids"]) == 2
    assert abs(zebra["direction_difference"] - 180) <= 20


@pytest.mark.django_db
def test_management_command_analyze_traffic_sign_data_v2(tmp_path):
    """The management command creates output CSV files for each report."""
    _create_db_entries()
    mount_file = os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv")
    sign_file = os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv")
    call_command(
        "analyze_traffic_sign_data_v2",
        mount_file=mount_file,
        sign_file=sign_file,
        previous_mount_file=mount_file,
        previous_sign_file=sign_file,
        output_dir=str(tmp_path),
        delimiter=",",
    )
    csv_files = [f for f in os.listdir(tmp_path) if f.endswith(".csv")]
    assert len(csv_files) > 0
    for pattern in ["status_distribution_analysis", "duplicate_signs_on_same_mount_analysis"]:
        assert any(pattern in f for f in csv_files), f"Expected report '{pattern}' not found"


# ===========================================================================
# Regression tests for csv_ssurl in mismatch report
# ===========================================================================


@pytest.mark.django_db
def test_status_mismatch_report_includes_csv_ssurl(tmp_path):
    """Every result in the status mismatch report must contain csv_ssurl."""
    _create_db_entries()
    analyzer = TrafficSignAnalyzerV2(
        os.path.join(TEST_FILES_DIR, "basic_mounts_v2.csv"),
        os.path.join(TEST_FILES_DIR, "basic_signs_v2.csv"),
        delimiter=",",
        output_dir=str(tmp_path),
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "STATUS AND INTERNAL_STATUS MISMATCH")
    for result in report["results"]:
        assert "csv_ssurl" in result, f"Missing csv_ssurl: {result}"


@pytest.mark.django_db
def test_status_mismatch_report_csv_ssurl_value(tmp_path: Path) -> None:  # noqa: F811
    """csv_ssurl in mismatch report matches the ssurl value from the CSV row.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    device_type, _ = TrafficControlDeviceType.objects.get_or_create(code="C39")
    TrafficSignRealFactory(source_id="sign_existing", source_name="StreetScan", device_type=device_type)

    expected_ssurl = "https://example.com/photo_123"
    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("mount_1")],
        [_sign_row("sign_existing", "mount_1", "New", "C39", color="2", ssurl=expected_ssurl)],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "STATUS AND INTERNAL_STATUS MISMATCH")
    sign_results = [r for r in report["results"] if r.get("source_id") == "sign_existing"]
    assert len(sign_results) == 1
    assert sign_results[0]["csv_ssurl"] == expected_ssurl


# ===========================================================================
# CodeTransformMixin unit tests (pure logic, no database)
# ===========================================================================


class _MixinStub(CodeTransformMixin):
    """Minimal concrete stub for CodeTransformMixin unit tests."""

    def __init__(self) -> None:
        self.code_replacements: list[dict] = []
        self.code_replacement_failures: list[dict] = []
        self.enriched_signs: list[dict] = []
        self.filtered_signs: list[dict] = []
        self.delimiter = ","

    def _row_to_csv_line(self, row: dict, delimiter: str) -> str:
        """Return empty string; not relevant for mixin unit tests."""
        return ""


def _stub_row(code: str, color: str = "", numero: str = "", loc_spec: str = "", source_id: str = "s1") -> dict:
    """Build a minimal CSV-like row dict for mixin tests.

    Args:
        code (str): Device type code value.
        color (str): Color field value.
        numero (str): Number code field value.
        loc_spec (str): Location specifier field value.
        source_id (str): Source id value.

    Returns:
        dict: Row dictionary with required keys.
    """
    return {
        CSVHeadersV2.id: source_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.color: color,
        CSVHeadersV2.number_code: numero,
        CSVHeadersV2.location_specifier: loc_spec,
    }


# ---------------------------------------------------------------------------
# _apply_code_and_color_transformation
# ---------------------------------------------------------------------------


def test_code_and_color_transformation_passthrough_for_unknown_code() -> None:
    """_apply_code_and_color_transformation leaves row unchanged when code is not in config dict.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("C39", color="1")
    stub._apply_code_and_color_transformation(row)
    assert row[CSVHeadersV2.code] == "C39"
    assert stub.code_replacements == []
    assert stub.code_replacement_failures == []


# ---------------------------------------------------------------------------
# _apply_code_and_color_no_color
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,expected_failure",
    [
        ("853_2", True),  # color_1_suffix="S", color_2_suffix="K" → both non-None → failure
        ("854", True),  # color_1_suffix="S", color_2_suffix="K" → both non-None → failure
    ],
)
def test_code_and_color_no_color_both_suffixes_required_produces_failure(code: str, expected_failure: bool) -> None:
    """_apply_code_and_color_no_color records failure when both suffixes are non-None and color missing.

    Args:
        code (str): Device type code with two non-None suffixes.
        expected_failure (bool): Whether a failure record is expected.

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CODE_AND_COLOR_DEPENDENT_CODES

    stub = _MixinStub()
    config = CODE_AND_COLOR_DEPENDENT_CODES[code]
    row = _stub_row(code)
    stub._apply_code_and_color_no_color(row, code, config["new_code"], config)
    assert row[CSVHeadersV2.code] == code
    assert len(stub.code_replacement_failures) == 1
    assert stub.code_replacement_failures[0]["reason"] == "missing_color_field"
    assert stub.code_replacements == []


@pytest.mark.parametrize(
    "code",
    [
        "H19_3",  # color_1_suffix="S", color_2_suffix=None → one suffix is None
        "827",  # color_1_suffix="S", color_2_suffix=None
        "845",  # color_1_suffix=None, color_2_suffix="K"
    ],
)
def test_code_and_color_no_color_one_suffix_none_produces_replacement(code: str) -> None:
    """_apply_code_and_color_no_color records a replacement when at least one suffix is None.

    Args:
        code (str): Device type code where one suffix is None.

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CODE_AND_COLOR_DEPENDENT_CODES

    stub = _MixinStub()
    config = CODE_AND_COLOR_DEPENDENT_CODES[code]
    base_code = config["new_code"]
    row = _stub_row(code)
    stub._apply_code_and_color_no_color(row, code, base_code, config)
    assert row[CSVHeadersV2.code] == base_code
    assert len(stub.code_replacements) == 1
    assert stub.code_replacements[0]["replacement_type"] == "code_and_color_based_no_color"
    assert stub.code_replacement_failures == []


# ---------------------------------------------------------------------------
# _apply_code_and_color_with_valid_color
# ---------------------------------------------------------------------------


def test_code_and_color_with_valid_color_invalid_color_value_produces_failure() -> None:
    """_apply_code_and_color_with_valid_color records failure for color not in ['1','2'].

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CODE_AND_COLOR_DEPENDENT_CODES

    stub = _MixinStub()
    code = "853_2"
    config = CODE_AND_COLOR_DEPENDENT_CODES[code]
    row = _stub_row(code, color="X")
    stub._apply_code_and_color_with_valid_color(row, code, config["new_code"], config, "X")
    assert row[CSVHeadersV2.code] == code
    assert len(stub.code_replacement_failures) == 1
    assert stub.code_replacement_failures[0]["reason"] == "invalid_color_value"


@pytest.mark.parametrize(
    "code,color,expected_new_code",
    [
        ("853_2", "1", "8531S"),  # color_1_suffix="S"
        ("853_2", "2", "8531K"),  # color_2_suffix="K"
        ("854", "1", "8541S"),
        ("854", "2", "8541K"),
    ],
)
def test_code_and_color_with_valid_color_applies_suffix(code: str, color: str, expected_new_code: str) -> None:
    """_apply_code_and_color_with_valid_color sets base_code + suffix on row for valid colors.

    Args:
        code (str): Original device type code.
        color (str): Color value ('1' or '2').
        expected_new_code (str): Expected new code after transformation.

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CODE_AND_COLOR_DEPENDENT_CODES

    stub = _MixinStub()
    config = CODE_AND_COLOR_DEPENDENT_CODES[code]
    row = _stub_row(code, color=color)
    stub._apply_code_and_color_with_valid_color(row, code, config["new_code"], config, color)
    assert row[CSVHeadersV2.code] == expected_new_code
    assert len(stub.code_replacements) == 1
    assert stub.code_replacements[0]["replacement_type"] == "code_and_color_based"


@pytest.mark.parametrize(
    "code,color,expected_new_code",
    [
        ("H19_3", "2", "H19.1_2"),  # color_2_suffix=None → suffix omitted → base_code only
        ("827", "2", "827"),  # color_2_suffix=None
        ("845", "1", "845"),  # color_1_suffix=None
    ],
)
def test_code_and_color_with_valid_color_none_suffix_uses_base_code(
    code: str, color: str, expected_new_code: str
) -> None:
    """_apply_code_and_color_with_valid_color sets base_code on row when suffix is None.

    Args:
        code (str): Original device type code.
        color (str): Color value ('1' or '2').
        expected_new_code (str): Expected new code (base_code only, no suffix).

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import CODE_AND_COLOR_DEPENDENT_CODES

    stub = _MixinStub()
    config = CODE_AND_COLOR_DEPENDENT_CODES[code]
    row = _stub_row(code, color=color)
    stub._apply_code_and_color_with_valid_color(row, code, config["new_code"], config, color)
    assert row[CSVHeadersV2.code] == expected_new_code
    assert stub.code_replacements[0]["suffix"] == "none"
    assert stub.code_replacement_failures == []


# ---------------------------------------------------------------------------
# _apply_code_and_color_transformation (integration through the dispatcher)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,color,expected_new_code,expected_type",
    [
        ("853_2", "", "853_2", None),  # both suffixes required, no color → failure, code unchanged
        ("H19_3", "", "H19.1_2", "code_and_color_based_no_color"),
        ("853_2", "1", "8531S", "code_and_color_based"),
        ("853_2", "2", "8531K", "code_and_color_based"),
        ("H19_3", "2", "H19.1_2", "code_and_color_based"),
    ],
)
def test_apply_code_and_color_transformation_dispatch(
    code: str, color: str, expected_new_code: str, expected_type: str | None
) -> None:
    """_apply_code_and_color_transformation dispatches correctly to sub-methods.

    Args:
        code (str): Device type code.
        color (str): Color field value.
        expected_new_code (str): Expected code on row after transformation.
        expected_type (str | None): Expected replacement_type, or None if failure expected.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row(code, color=color)
    stub._apply_code_and_color_transformation(row)
    assert row[CSVHeadersV2.code] == expected_new_code
    if expected_type is not None:
        assert len(stub.code_replacements) == 1
        assert stub.code_replacements[0]["replacement_type"] == expected_type
    else:
        assert len(stub.code_replacement_failures) == 1


# ---------------------------------------------------------------------------
# _apply_number_code_from_code_extraction
# ---------------------------------------------------------------------------


def test_number_code_from_code_extraction_no_underscore_passthrough() -> None:
    """_apply_number_code_from_code_extraction leaves row unchanged when no underscore present.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344NOUNDERSCORE")
    stub._apply_number_code_from_code_extraction(row, "344NOUNDERSCORE", "12", "344")
    assert row[CSVHeadersV2.code] == "344NOUNDERSCORE"
    assert stub.code_replacements == []


def test_number_code_from_code_extraction_mismatch_passthrough() -> None:
    """_apply_number_code_from_code_extraction leaves row unchanged when extracted number mismatches.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_99")
    stub._apply_number_code_from_code_extraction(row, "344_99", "12", "344")
    assert row[CSVHeadersV2.code] == "344_99"
    assert stub.code_replacements == []


def test_number_code_from_code_extraction_match_produces_replacement() -> None:
    """_apply_number_code_from_code_extraction replaces code on row when extracted number matches.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12")
    stub._apply_number_code_from_code_extraction(row, "344_12", "12", "344")
    assert row[CSVHeadersV2.code] == "344"
    assert len(stub.code_replacements) == 1
    assert stub.code_replacements[0]["replacement_type"] == "number_code_based"
    assert stub.code_replacements[0]["old_code"] == "344_12"
    assert stub.code_replacements[0]["new_code"] == "344"


# ---------------------------------------------------------------------------
# _apply_number_code_replacement
# ---------------------------------------------------------------------------


def test_number_code_replacement_matching_number_produces_replacement() -> None:
    """_apply_number_code_replacement replaces code on row when number_code matches expected.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12")
    stub._apply_number_code_replacement(row, "344_12", "344", "12", "12")
    assert row[CSVHeadersV2.code] == "344"
    assert len(stub.code_replacements) == 1
    assert stub.code_replacements[0]["replacement_type"] == "number_code_based"


def test_number_code_replacement_mismatching_number_produces_failure() -> None:
    """_apply_number_code_replacement records failure when number_code does not match expected.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12")
    stub._apply_number_code_replacement(row, "344_12", "344", "99", "12")
    assert row[CSVHeadersV2.code] == "344_12"
    assert len(stub.code_replacement_failures) == 1
    assert stub.code_replacement_failures[0]["reason"] == "number_code_mismatch"
    assert stub.code_replacement_failures[0]["expected_number"] == "12"
    assert stub.code_replacement_failures[0]["cleaned_number"] == "99"


def test_number_code_replacement_non_numeric_value_produces_failure() -> None:
    """_apply_number_code_replacement records failure for non-numeric number_code value.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12")
    stub._apply_number_code_replacement(row, "344_12", "344", "abc", "12")
    assert row[CSVHeadersV2.code] == "344_12"
    assert len(stub.code_replacement_failures) == 1
    assert stub.code_replacement_failures[0]["cleaned_number"] == ""


# ---------------------------------------------------------------------------
# _apply_number_code_validation
# ---------------------------------------------------------------------------


def test_number_code_validation_passthrough_for_unknown_code() -> None:
    """_apply_number_code_validation leaves row unchanged when not in NUMBER_CODE_DEPENDENT_CODES.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("C39")
    stub._apply_number_code_validation(row)
    assert row[CSVHeadersV2.code] == "C39"
    assert stub.code_replacements == []


def test_number_code_validation_no_number_code_field_uses_extraction() -> None:
    """_apply_number_code_validation falls back to code extraction when number_code is absent.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12")  # numero="" → extraction path
    stub._apply_number_code_validation(row)
    assert row[CSVHeadersV2.code] == "344"
    assert stub.code_replacements[0]["replacement_type"] == "number_code_based"


def test_number_code_validation_with_number_code_field_uses_replacement() -> None:
    """_apply_number_code_validation uses number_code field when present.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12", numero="12")
    stub._apply_number_code_validation(row)
    assert row[CSVHeadersV2.code] == "344"
    assert stub.code_replacements[0]["number_code_value"] == "12"


def test_number_code_validation_with_mismatching_number_code_produces_failure() -> None:
    """_apply_number_code_validation records failure when number_code does not match expected.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("344_12", numero="99")
    stub._apply_number_code_validation(row)
    assert row[CSVHeadersV2.code] == "344_12"
    assert len(stub.code_replacement_failures) == 1
    assert stub.code_replacement_failures[0]["reason"] == "number_code_mismatch"


# ---------------------------------------------------------------------------
# _apply_conditional_number_code_replacement
# ---------------------------------------------------------------------------


def test_conditional_number_code_passthrough_for_unknown_code() -> None:
    """_apply_conditional_number_code_replacement leaves row unchanged when not in config.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("C39")
    stub._apply_conditional_number_code_replacement(row)
    assert row[CSVHeadersV2.code] == "C39"
    assert stub.code_replacements == []


def test_conditional_number_code_passthrough_when_no_number_code() -> None:
    """_apply_conditional_number_code_replacement leaves row unchanged when number_code absent.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("363")  # numero="" → no match
    stub._apply_conditional_number_code_replacement(row)
    assert row[CSVHeadersV2.code] == "363"
    assert stub.code_replacements == []


def test_conditional_number_code_passthrough_when_number_not_in_map() -> None:
    """_apply_conditional_number_code_replacement leaves row unchanged when number not in replacements.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("363", numero="99")
    stub._apply_conditional_number_code_replacement(row)
    assert row[CSVHeadersV2.code] == "363"
    assert stub.code_replacements == []


def test_conditional_number_code_applies_replacement_when_number_matches() -> None:
    """_apply_conditional_number_code_replacement replaces code on row when number_code matches a key.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("363", numero="40")
    stub._apply_conditional_number_code_replacement(row)
    assert row[CSVHeadersV2.code] == "3635"
    assert len(stub.code_replacements) == 1
    assert stub.code_replacements[0]["replacement_type"] == "conditional_number_code"
    assert stub.code_replacements[0]["old_code"] == "363"
    assert stub.code_replacements[0]["new_code"] == "3635"


# ---------------------------------------------------------------------------
# _enrich_location_specifier
# ---------------------------------------------------------------------------


def test_enrich_location_specifier_sets_value_when_absent() -> None:
    """_enrich_location_specifier sets location_specifier to '4' when code is in list and value missing.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("4171", loc_spec="")
    stub._enrich_location_specifier(row)
    assert row[CSVHeadersV2.location_specifier] == "4"
    assert len(stub.enriched_signs) == 1
    assert stub.enriched_signs[0]["field"] == "location_specifier"
    assert stub.enriched_signs[0]["new_value"] == "4"
    assert stub.enriched_signs[0]["old_value"] is None


@pytest.mark.parametrize("code", ["4171", "4172", "418", "D3.1", "D3.1_2", "D3.2", "D3.2_2", "D3.3", "D3.3_2"])
def test_enrich_location_specifier_all_eligible_codes(code: str) -> None:
    """_enrich_location_specifier sets '4' for every code in LOCATION_SPECIFIER_4_CODES.

    Args:
        code (str): A code from LOCATION_SPECIFIER_4_CODES.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row(code, loc_spec="")
    stub._enrich_location_specifier(row)
    assert row[CSVHeadersV2.location_specifier] == "4"
    assert len(stub.enriched_signs) == 1


def test_enrich_location_specifier_no_change_when_value_exists() -> None:
    """_enrich_location_specifier does not overwrite an existing location_specifier value.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("4171", loc_spec="2")
    stub._enrich_location_specifier(row)
    assert row[CSVHeadersV2.location_specifier] == "2"
    assert stub.enriched_signs == []


def test_enrich_location_specifier_no_change_for_unknown_code() -> None:
    """_enrich_location_specifier does nothing when code is not in LOCATION_SPECIFIER_4_CODES.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("C39", loc_spec="")
    stub._enrich_location_specifier(row)
    assert row[CSVHeadersV2.location_specifier] == ""
    assert stub.enriched_signs == []


def test_enrich_internal_additional_info_records_enrichment() -> None:
    """_enrich_internal_additional_info appends to enriched_signs and sets row value.

    Returns:
        None
    """
    from traffic_control.analyze_utils.traffic_sign_data_v2_constants import INTERNAL_ADDITIONAL_INFO_ENRICHMENTS

    # pick the first code that has an enrichment
    code = next(iter(INTERNAL_ADDITIONAL_INFO_ENRICHMENTS))
    expected_value = INTERNAL_ADDITIONAL_INFO_ENRICHMENTS[code]
    stub = _MixinStub()
    row = _stub_row(code)
    stub._enrich_internal_additional_info(row)
    assert row["internal_additional_info"] == expected_value
    assert len(stub.enriched_signs) == 1
    assert stub.enriched_signs[0]["field"] == "internal_additional_info"
    assert stub.enriched_signs[0]["new_value"] == expected_value
    assert stub.enriched_signs[0]["old_value"] is None
    assert stub.enriched_signs[0]["code"] == code


def test_enrich_internal_additional_info_no_change_for_unknown_code() -> None:
    """_enrich_internal_additional_info does nothing when code has no enrichment entry.

    Returns:
        None
    """
    stub = _MixinStub()
    row = _stub_row("C39")
    row["internal_additional_info"] = None
    stub._enrich_internal_additional_info(row)
    assert row["internal_additional_info"] is None
    assert stub.enriched_signs == []


# ===========================================================================
# Active additional signs with removed parent report
# ===========================================================================


@pytest.mark.django_db
def test_removed_parent_traffic_sign_reported(tmp_path: Path) -> None:
    """Active additional sign referencing a Removed traffic sign is reported.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")
    TrafficControlDeviceType.objects.get_or_create(code="H24S")

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [
            _sign_row("parent1", "m1", "Removed", "C39"),
            _sign_row("add1", "m1", "New", "H24S", parent_id="parent1", ssurl="https://example.com/add"),
        ],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT")
    result = next((r for r in report["results"] if r["additional_sign_source_id"] == "add1"), None)

    assert result is not None
    assert result["parent_source_id"] == "parent1"
    assert result["parent_status"] == "Removed"
    assert result["parent_type"] == "traffic_sign"
    assert result["parent_code"] == "C39"
    assert result["additional_sign_ssurl"] == "https://example.com/add"


@pytest.mark.django_db
def test_removed_parent_signpost_reported(tmp_path: Path) -> None:
    """Active additional sign referencing a Removed signpost is reported.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="645")
    TrafficControlDeviceType.objects.get_or_create(code="H24S")

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [
            _sign_row("signpost1", "m1", "Removed", "645"),
            _sign_row("add2", "m1", "Unchanged", "H24S", parent_id="signpost1"),
        ],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT")
    result = next((r for r in report["results"] if r["additional_sign_source_id"] == "add2"), None)

    assert result is not None
    assert result["parent_source_id"] == "signpost1"
    assert result["parent_type"] == "signpost"
    assert result["parent_status"] == "Removed"


@pytest.mark.django_db
def test_removed_additional_sign_not_reported(tmp_path: Path) -> None:
    """Additional sign that is itself Removed is excluded from the report even if parent is Removed.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")
    TrafficControlDeviceType.objects.get_or_create(code="H24S")

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [
            _sign_row("parent_removed", "m1", "Removed", "C39"),
            _sign_row("add_removed", "m1", "Removed", "H24S", parent_id="parent_removed"),
        ],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT")
    ids = [r["additional_sign_source_id"] for r in report["results"]]
    assert "add_removed" not in ids


@pytest.mark.django_db
def test_active_additional_sign_with_active_parent_not_reported(tmp_path: Path) -> None:
    """Additional sign referencing an active (non-Removed) parent is not reported.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="C39")
    TrafficControlDeviceType.objects.get_or_create(code="H24S")

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [
            _sign_row("parent_active", "m1", "Unchanged", "C39"),
            _sign_row("add_active", "m1", "New", "H24S", parent_id="parent_active"),
        ],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT")
    ids = [r["additional_sign_source_id"] for r in report["results"]]
    assert "add_active" not in ids


@pytest.mark.django_db
def test_additional_sign_with_no_parent_not_reported(tmp_path: Path) -> None:
    """Additional sign with a blank parent ID is not reported.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    MountType.objects.get_or_create(code="POLE", description="POLE", description_fi="Pylväs")
    TrafficControlDeviceType.objects.get_or_create(code="H24S")

    analyzer = _make_analyzer(
        tmp_path,
        [_mount_row("m1")],
        [_sign_row("add_no_parent", "m1", "New", "H24S", parent_id="")],
    )
    report = next(r for r in analyzer.analyze() if r["REPORT_TYPE"] == "ACTIVE ADDITIONAL SIGNS WITH REMOVED PARENT")
    ids = [r["additional_sign_source_id"] for r in report["results"]]
    assert "add_no_parent" not in ids


# ---------------------------------------------------------------------------
# _enrich_number_code_from_teksti
# ---------------------------------------------------------------------------


def _stub_row_with_teksti(
    code: str,
    numero: str = "",
    teksti: str = "",
    source_id: str = "s1",
) -> dict:
    """Build a minimal CSV-like row dict including the teksti field.

    Args:
        code (str): Device type code value.
        numero (str): Number code field value.
        teksti (str): teksti field value.
        source_id (str): Source id value.

    Returns:
        dict: Row dictionary with required keys.
    """
    return {
        CSVHeadersV2.id: source_id,
        CSVHeadersV2.code: code,
        CSVHeadersV2.number_code: numero,
        CSVHeadersV2.txt: teksti,
        CSVHeadersV2.color: "",
        CSVHeadersV2.location_specifier: "",
    }


def test_enrich_number_code_from_teksti_passthrough_for_unknown_code() -> None:
    """_enrich_number_code_from_teksti leaves row unchanged when code is not in NUMBER_CODE_DEPENDENT_NEW_CODES.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("999", teksti="30 t")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == ""
    assert stub.enriched_signs == []


def test_enrich_number_code_from_teksti_passthrough_when_number_code_already_set() -> None:
    """_enrich_number_code_from_teksti leaves row unchanged when number_code already has a value.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("344", numero="12", teksti="30 t")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == "12"
    assert stub.enriched_signs == []


def test_enrich_number_code_from_teksti_passthrough_when_teksti_has_no_leading_number() -> None:
    """_enrich_number_code_from_teksti leaves row unchanged when teksti contains no leading integer.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("344", teksti="no number here")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == ""
    assert stub.enriched_signs == []


def test_enrich_number_code_from_teksti_passthrough_when_teksti_empty() -> None:
    """_enrich_number_code_from_teksti leaves row unchanged when teksti is empty.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("344", teksti="")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == ""
    assert stub.enriched_signs == []


def test_enrich_number_code_from_teksti_extracts_plain_number() -> None:
    """_enrich_number_code_from_teksti sets number_code from a plain integer in teksti.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("344", teksti="12")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == "12"
    assert stub.enriched_signs[0]["field"] == "number_code"
    assert stub.enriched_signs[0]["new_value"] == "12"


def test_enrich_number_code_from_teksti_extracts_number_with_unit() -> None:
    """_enrich_number_code_from_teksti extracts leading integer even when teksti has a unit suffix.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("344", teksti="30 t")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == "30"
    assert stub.enriched_signs[0]["new_value"] == "30"


def test_enrich_number_code_from_teksti_extracts_number_with_leading_whitespace() -> None:
    """_enrich_number_code_from_teksti handles leading whitespace in teksti.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("345", teksti="  60 km/h")
    stub._enrich_number_code_from_teksti(row)
    assert row[CSVHeadersV2.number_code] == "60"
    assert stub.enriched_signs[0]["source_id"] == "s1"


def test_enrich_number_code_from_teksti_records_correct_enriched_sign_entry() -> None:
    """_enrich_number_code_from_teksti records old_value as None and correct code in enriched_signs.

    Args: None
    Returns: None
    """
    stub = _MixinStub()
    row = _stub_row_with_teksti("346", teksti="8 t", source_id="abc")
    stub._enrich_number_code_from_teksti(row)
    entry = stub.enriched_signs[0]
    assert entry["source_id"] == "abc"
    assert entry["code"] == "346"
    assert entry["field"] == "number_code"
    assert entry["old_value"] is None
    assert entry["new_value"] == "8"
