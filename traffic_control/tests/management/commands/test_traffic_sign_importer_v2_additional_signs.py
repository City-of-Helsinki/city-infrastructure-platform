"""Tests for TrafficSignImporterV2 additional sign phases: create, update, deactivate."""
import csv
import datetime
from pathlib import Path

import pytest
from django.contrib.gis.geos import Point

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME, TrafficSignImporterV2
from traffic_control.enums import Lifecycle
from traffic_control.models import AdditionalSignReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountTypeFactory,
    OwnerFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignRealFactory,
)

# ---------------------------------------------------------------------------
# CSV helpers  (shared layout with signs / signpost test modules)
# ---------------------------------------------------------------------------

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
    "recordedat",
    "korkeus",
    "ssurl",
]

_COORDS = ["25497188.0", "6673461.0", "8.0", "0.01", "0.01", "0.01"]
_TS = "2023/08/15 12:00:00+00"
# Additional sign codes start with H or 8.
_AS_CODE = "H17"


def _sign_row(
    obj_id: str,
    code: str = _AS_CODE,
    status: str = "New",
    x: str = _COORDS[0],
    y: str = _COORDS[1],
    mount_id: str = "",
    parent_sign_id: str = "",
    txt: str = "",
    scanned_at: str = _TS,
    ssurl: str = "",
    number_code: str = "",
) -> list[str]:
    """Build a sign CSV row for an additional sign.

    Args:
        obj_id (str): Source identifier.
        code (str): Device type code; must start with H or 8.
        status (str): CSV status field.
        x (str): X coordinate (EPSG:3879).
        y (str): Y coordinate (EPSG:3879).
        mount_id (str): kiinnityskohta_id value.
        parent_sign_id (str): lisäkilven_päämerkin_id value.
        txt (str): teksti value.
        scanned_at (str): recordedat timestamp.
        ssurl (str): Attachment URL.
        number_code (str): numerokoodi value.

    Returns:
        list[str]: Field values for one CSV row.
    """
    return [
        "1",
        obj_id,
        x,
        y,
        _COORDS[2],
        _COORDS[3],
        _COORDS[4],
        _COORDS[5],
        mount_id,
        status,
        code,
        txt,
        "",
        "",
        "",
        number_code,
        "",
        "",
        "",
        parent_sign_id,
        scanned_at,
        "2.5",
        ssurl,
    ]


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> str:
    """Write a CSV file and return its absolute path.

    Args:
        path (Path): Directory to write into.
        header (list[str]): Column headers.
        rows (list[list[str]]): Data rows.

    Returns:
        str: Absolute path of the written file.
    """
    file_path = path / f"test_{id(rows)}.csv"
    with file_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    return str(file_path)


def _make_importer(
    tmp_path: Path,
    sign_rows: list[list[str]],
    mount_rows: list[list[str]] | None = None,
    *,
    dry_run: bool = False,
    force_update: bool = False,
    phases: list[str] | None = None,
) -> TrafficSignImporterV2:
    """Build a TrafficSignImporterV2 configured for additional sign tests.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.
        sign_rows (list[list[str]]): Sign CSV data rows.
        mount_rows (list[list[str]] | None): Mount CSV rows; defaults to empty.
        dry_run (bool): Whether to enable dry-run mode.
        force_update (bool): Whether to enable force-update mode.
        phases (list[str] | None): Phases to run; defaults to ``["create"]``.

    Returns:
        TrafficSignImporterV2: Configured importer instance.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows or [])
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, sign_rows)
    return TrafficSignImporterV2(
        mount_file=mf,
        sign_file=sf,
        object_types=["additional-signs"],
        phases=phases or ["create"],
        dry_run=dry_run,
        force_update=force_update,
        delimiter=",",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_owner(db):
    """Create the default owner required by _get_default_owner().

    Args:
        db: Pytest-django db fixture.

    Returns:
        Owner: The created owner instance.
    """
    return OwnerFactory(name_fi="Helsingin kaupunki", name_en="City of Helsinki")


@pytest.fixture()
def device_type(db):
    """Create a TrafficControlDeviceType matching the additional sign code.

    Args:
        db: Pytest-django db fixture.

    Returns:
        TrafficControlDeviceType: The created device type instance.
    """
    return TrafficControlDeviceTypeFactory(code=_AS_CODE)


@pytest.fixture()
def mount_type(db):
    """Create a MountType fixture.

    Args:
        db: Pytest-django db fixture.

    Returns:
        MountType: The created mount type instance.
    """
    return MountTypeFactory(description="POLE", description_fi="Pylväs")


# ===========================================================================
# _create_additional_signs
# ===========================================================================


@pytest.mark.django_db
def test_create_additional_signs_inserts_new_records(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """New additional sign rows are inserted into the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("AS1"), _sign_row("AS2")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id__in=["AS1", "AS2"], source_name=SOURCE_NAME).count() == 2


@pytest.mark.django_db
def test_create_additional_signs_sets_lifecycle_active(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Created additional signs have lifecycle set to ACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASLC")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASLC")
    assert obj.lifecycle == Lifecycle.ACTIVE


@pytest.mark.django_db
def test_create_additional_signs_sets_missing_content_true(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Created additional signs have missing_content set to True.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASMC")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASMC")
    assert obj.missing_content is True


@pytest.mark.django_db
def test_create_additional_signs_composes_additional_information(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """additional_information is composed from teksti and numerokoodi.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASAI", txt="hello", number_code="50")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASAI")
    assert obj.additional_information == "text:hello; numbercode:50"


@pytest.mark.django_db
def test_create_additional_signs_skips_removed_status(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows with status='Removed' are not inserted.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASRM", status="Removed")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASRM").count() == 0
    assert summary["additional_signs_created"] == 0


@pytest.mark.django_db
def test_create_additional_signs_skips_unreadable_text(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows whose teksti is 'unreadable' (case-insensitive) are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASUR", txt="Unreadable")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASUR").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASUR" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_additional_signs_skips_invalid_coordinates(tmp_path: Path, default_owner, device_type) -> None:
    """Rows with non-numeric coordinates are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASBD", x="NOT_NUM", y="BAD")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASBD").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASBD" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_additional_signs_skips_unknown_device_type_code(tmp_path: Path, default_owner, mount_type) -> None:
    """Rows whose device type code is not in the DB are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASUNK", code="H_DOESNOTEXIST")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASUNK").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASUNK" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_additional_signs_skips_already_existing(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows whose source_id already exists in the DB are not inserted again.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASEXIST",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASEXIST"), _sign_row("ASNEW")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASEXIST").count() == 1
    assert AdditionalSignReal.objects.filter(source_id="ASNEW").count() == 1


@pytest.mark.django_db
def test_create_additional_signs_warning_for_unresolved_mount(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A row referencing a non-existent mount is imported with a warning.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASWM", mount_id="NONEXISTENT")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASWM").count() == 1
    warnings = [e for e in summary["details"] if e["source_id"] == "ASWM" and e["level"] == "warning"]
    assert len(warnings) == 1


@pytest.mark.django_db
def test_create_additional_signs_parent_resolved_to_traffic_sign(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """parent_sign_id matching a TrafficSignReal is resolved to parent FK.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    ts = TrafficSignRealFactory(
        source_id="TS_PARENT",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
    )

    importer = _make_importer(tmp_path, [_sign_row("AS_KID", parent_sign_id="TS_PARENT")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="AS_KID")
    assert obj.parent_id == ts.pk
    assert obj.signpost_real_id is None


@pytest.mark.django_db
def test_create_additional_signs_parent_resolved_to_signpost(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """parent_sign_id matching a SignpostReal is resolved to signpost_real FK.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    sp = SignpostRealFactory(
        source_id="SP_PARENT",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
    )

    importer = _make_importer(tmp_path, [_sign_row("AS_SPKID", parent_sign_id="SP_PARENT")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="AS_SPKID")
    assert obj.signpost_real_id == sp.pk
    assert obj.parent_id is None


@pytest.mark.django_db
def test_create_additional_signs_warning_for_unresolved_parent(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """An unknown parent_sign_id is imported without parent and with a warning.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASNOP", parent_sign_id="MISSING_PARENT")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASNOP")
    assert obj.parent_id is None
    assert obj.signpost_real_id is None
    warnings = [e for e in summary["details"] if e["source_id"] == "ASNOP" and e["level"] == "warning"]
    assert len(warnings) == 1


@pytest.mark.django_db
def test_create_additional_signs_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_create_additional_signs writes a phase_results entry.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASPR1"), _sign_row("ASPR2")])
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    result = summary.get("phase_results", {}).get("additional-signs", {}).get("create")
    assert result is not None
    assert result["created"] == 2


@pytest.mark.django_db
def test_create_additional_signs_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode no records are written but count reflects candidates.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASDRY")], dry_run=True)
    summary: dict = {"details": []}
    importer._create_additional_signs(summary)

    assert AdditionalSignReal.objects.filter(source_id="ASDRY").count() == 0
    assert summary["additional_signs_created"] == 1


# ===========================================================================
# _update_additional_signs
# ===========================================================================


@pytest.mark.django_db
def test_update_additional_signs_updates_existing_record(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """An existing additional sign with a changed location is updated in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASU1",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASU1")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASU1")
    assert obj.location.x == pytest.approx(25497188.0, abs=1)
    assert summary["additional_signs_updated"] == 1


@pytest.mark.django_db
def test_update_additional_signs_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Updated additional signs have updated_at populated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASUA",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASUA")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASUA")
    assert obj.updated_at is not None


@pytest.mark.django_db
def test_update_additional_signs_skips_unchanged_record(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A record whose CSV values match the DB is skipped (not re-written).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASUNC",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        direction=None,
        height=250,
        scanned_at=None,
        attachment_url="",
        additional_information="text:; numbercode:",
        condition=None,
        location_specifier=None,
        mount_real=None,
        mount_type=None,
        parent=None,
        signpost_real=None,
        color=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASUNC", scanned_at="")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0
    result = summary["phase_results"]["additional-signs"]["update"]
    assert result["skipped"] >= 1


@pytest.mark.django_db
def test_update_additional_signs_force_update_bypasses_comparison(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """With force_update=True, even unchanged records are re-written.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASFU",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        direction=None,
        height=250,
        scanned_at=None,
        attachment_url="",
        additional_information="text:; numbercode:",
        condition=None,
        location_specifier=None,
        mount_real=None,
        mount_type=None,
        parent=None,
        signpost_real=None,
        color=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASFU", scanned_at="")], force_update=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 1


@pytest.mark.django_db
def test_update_additional_signs_skips_removed_rows(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows with status='Removed' are not touched by the update phase.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASURM",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASURM", status="Removed")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0


@pytest.mark.django_db
def test_update_additional_signs_skips_unreadable_text(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A row with teksti='unreadable' is skipped during update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASUURT",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASUURT", txt="unreadable")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASUURT" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_additional_signs_skips_invalid_coordinates(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A CSV row with invalid coordinates is skipped during update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASBDU",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASBDU", x="NOT_NUM", y="BAD")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASBDU" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_additional_signs_skips_unknown_device_type_code(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A row with an unknown device type code is skipped during update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASUKC",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASUKC", code="H_NOTEXIST")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ASUKC" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_additional_signs_ignores_rows_not_in_db(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """CSV rows with no matching DB record are silently ignored by update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASNONEX")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    assert summary["additional_signs_updated"] == 0


@pytest.mark.django_db
def test_update_additional_signs_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, existing additional signs are not modified in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDRYU",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDRYU")], dry_run=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDRYU")
    assert obj.location.x == pytest.approx(25497100.0, abs=1)
    assert summary["additional_signs_updated"] == 1


@pytest.mark.django_db
def test_update_additional_signs_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_update_additional_signs writes a phase_results entry.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASPH2",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASPH2")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_additional_signs(summary)

    result = summary.get("phase_results", {}).get("additional-signs", {}).get("update")
    assert result is not None
    assert result["updated"] == 1
    assert "skipped" in result


# ===========================================================================
# _deactivate_additional_signs
# ===========================================================================


@pytest.mark.django_db
def test_deactivate_additional_signs_sets_lifecycle_inactive(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Deactivation sets lifecycle to INACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDEA1",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDEA1", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDEA1")
    assert obj.lifecycle == Lifecycle.INACTIVE


@pytest.mark.django_db
def test_deactivate_additional_signs_sets_validity_period_end(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Deactivation sets validity_period_end to the scanned_at date from CSV.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDEA2",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDEA2", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDEA2")
    assert obj.validity_period_end == datetime.date(2023, 8, 15)


@pytest.mark.django_db
def test_deactivate_additional_signs_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation populates updated_at on the record.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDEA3",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDEA3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDEA3")
    assert obj.updated_at is not None


@pytest.mark.django_db
def test_deactivate_additional_signs_stamps_source_name(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets source_name to StreetScan2025.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDEA4",
        source_name="StreetScan",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDEA4", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDEA4")
    assert obj.source_name == SOURCE_NAME


@pytest.mark.django_db
def test_deactivate_additional_signs_skips_non_removed_rows(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Non-Removed rows are not deactivated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASNRM",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASNRM", status="Changed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASNRM")
    assert obj.lifecycle == Lifecycle.ACTIVE
    assert summary["additional_signs_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_additional_signs_skips_rows_not_in_db(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Removed rows with no matching DB record are silently skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ASGHOST", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    assert summary["additional_signs_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_additional_signs_dry_run_does_not_write(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """In dry-run mode, additional signs are not deactivated in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASDRYD",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASDRYD", status="Removed")], dry_run=True, phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    obj = AdditionalSignReal.objects.get(source_id="ASDRYD")
    assert obj.lifecycle == Lifecycle.ACTIVE
    assert summary["additional_signs_deactivated"] == 1


@pytest.mark.django_db
def test_deactivate_additional_signs_phase_result_recorded(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """_deactivate_additional_signs writes a phase_results entry.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    AdditionalSignRealFactory(
        source_id="ASPH3",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        parent=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("ASPH3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_additional_signs(summary)

    result = summary.get("phase_results", {}).get("additional-signs", {}).get("deactivate")
    assert result is not None
    assert result["deactivated"] == 1
