"""Tests for TrafficSignImporterV2 traffic sign phases: create, update, deactivate."""
from __future__ import annotations

import csv
import datetime
from pathlib import Path

import pytest
from django.contrib.gis.geos import Point

from traffic_control.analyze_utils.traffic_sign_data_v2_import import TrafficSignImporterV2
from traffic_control.enums import Lifecycle
from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import (
    MountTypeFactory,
    OwnerFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignRealFactory,
)

# ---------------------------------------------------------------------------
# CSV helpers
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

# Valid Helsinki-area EPSG:3879 coordinates
_COORDS = ["25497188.0", "6673461.0", "8.0", "0.01", "0.01", "0.01"]
_TS = "2023/08/15 12:00:00+00"
_SIGN_CODE = "A11"


def _sign_row(
    obj_id: str,
    code: str = _SIGN_CODE,
    status: str = "New",
    x: str = _COORDS[0],
    y: str = _COORDS[1],
    mount_id: str = "",
    parent_sign_id: str = "",
    txt: str = "",
    scanned_at: str = _TS,
    ssurl: str = "",
) -> list[str]:
    """Build a sign CSV row.

    Args:
        obj_id (str): Object identifier used as source_id.
        code (str): Device type code (merkkikoodi).
        status (str): CSV status field value.
        x (str): X coordinate.
        y (str): Y coordinate.
        mount_id (str): kiinnityskohta_id value.
        parent_sign_id (str): lisäkilven_päämerkin_id value.
        txt (str): teksti value.
        scanned_at (str): recordedat timestamp.
        ssurl (str): Attachment URL.

    Returns:
        list[str]: Field values for one sign row.
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
        "",
        "",
        "",
        "",
        parent_sign_id,
        scanned_at,
        "2.5",
        ssurl,
    ]


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> str:
    """Write a CSV file and return its path.

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
    """Build a TrafficSignImporterV2 configured for sign tests.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.
        sign_rows (list[list[str]]): Sign CSV data rows.
        mount_rows (list[list[str]] | None): Mount CSV data rows; defaults to empty.
        dry_run (bool): Whether to enable dry-run mode.
        force_update (bool): Whether to enable force-update mode.
        phases (list[str] | None): Phases to run; defaults to the phase under test.

    Returns:
        TrafficSignImporterV2: Configured importer instance.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows or [])
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, sign_rows)
    return TrafficSignImporterV2(
        mount_file=mf,
        sign_file=sf,
        object_types=["signs"],
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
    """Create a TrafficControlDeviceType with code matching _SIGN_CODE.

    Args:
        db: Pytest-django db fixture.

    Returns:
        TrafficControlDeviceType: The created device type instance.
    """
    return TrafficControlDeviceTypeFactory(code=_SIGN_CODE)


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
# _create_signs — basic creation
# ===========================================================================


@pytest.mark.django_db
def test_create_signs_inserts_new_records(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """New sign rows are inserted into the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("S1"), _sign_row("S2")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id__in=["S1", "S2"], source_name="StreetScan2025").count() == 2


@pytest.mark.django_db
def test_create_signs_sets_lifecycle_active(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Created signs have lifecycle set to ACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("LC1")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="LC1")
    assert sign.lifecycle == Lifecycle.ACTIVE


@pytest.mark.django_db
def test_create_signs_sets_created_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Created signs have created_at populated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("CA1")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="CA1")
    assert sign.created_at is not None


@pytest.mark.django_db
def test_create_signs_skips_removed_status(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows with status='Removed' are not inserted.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("RM1", status="Removed")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="RM1").count() == 0
    assert summary["signs_created"] == 0


@pytest.mark.django_db
def test_create_signs_skips_invalid_coordinates(tmp_path: Path, default_owner, device_type) -> None:
    """Rows with non-numeric coordinates are skipped with a skip detail entry.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("BAD", x="NOT_NUM", y="BAD")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="BAD").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "BAD" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_signs_skips_zero_coordinates(tmp_path: Path, default_owner, device_type) -> None:
    """Rows with (0, 0) coordinates fail geometry check and are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("ZERO", x="0.0", y="0.0")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="ZERO").count() == 0


@pytest.mark.django_db
def test_create_signs_skips_unknown_device_type_code(tmp_path: Path, default_owner, mount_type) -> None:
    """Rows whose device type code is not in the DB are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("UNK", code="DOESNOTEXIST")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="UNK").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "UNK" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_signs_skips_already_existing_source_ids(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows whose source_id already exists in the DB are not inserted again.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="EXIST",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
    )
    importer = _make_importer(tmp_path, [_sign_row("EXIST"), _sign_row("NEW")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="EXIST").count() == 1
    assert TrafficSignReal.objects.filter(source_id="NEW").count() == 1


@pytest.mark.django_db
def test_create_signs_warning_for_unresolved_mount(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A sign referencing a non-existent mount is imported with a warning.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("WM1", mount_id="NONEXISTENT_MOUNT")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="WM1").count() == 1
    warnings = [e for e in summary["details"] if e["source_id"] == "WM1" and e["level"] == "warning"]
    assert len(warnings) == 1


@pytest.mark.django_db
def test_create_signs_warning_for_parent_sign_id(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A sign carrying parent_sign_id is imported with a warning (field ignored).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("PS1", parent_sign_id="some_parent_id")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="PS1").count() == 1
    warnings = [e for e in summary["details"] if e["source_id"] == "PS1" and e["level"] == "warning"]
    assert len(warnings) == 1


@pytest.mark.django_db
def test_create_signs_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_create_signs writes a phase_results entry for ('signs', 'create').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("PR1"), _sign_row("PR2")])
    summary: dict = {"details": []}
    importer._create_signs(summary)

    result = summary.get("phase_results", {}).get("signs", {}).get("create")
    assert result is not None
    assert result["created"] == 2


@pytest.mark.django_db
def test_create_signs_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, no TrafficSignReal records are written.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("DRY1")], dry_run=True)
    summary: dict = {"details": []}
    importer._create_signs(summary)

    assert TrafficSignReal.objects.filter(source_id="DRY1").count() == 0
    assert summary["signs_created"] == 1


# ===========================================================================
# _update_signs — basic update
# ===========================================================================


@pytest.mark.django_db
def test_update_signs_updates_existing_record(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """An existing sign with a changed location is updated in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="U1",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("U1")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="U1")
    # Location changed → updated_at set, location refreshed
    assert sign.location.x == pytest.approx(25497188.0, abs=1)
    assert summary["signs_updated"] == 1


@pytest.mark.django_db
def test_update_signs_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Updated signs have updated_at populated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="UA1",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("UA1")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="UA1")
    assert sign.updated_at is not None


@pytest.mark.django_db
def test_update_signs_skips_unchanged_record(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A sign whose CSV values match DB values is not updated (skipped).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="UNC",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        direction=None,
        height=250,  # CSV korkeus="2.5" → int(2.5*100)=250
        scanned_at=None,
        attachment_url="",
        txt=None,
        value=None,
        condition=None,
        location_specifier=None,
        mount_real=None,
        mount_type=None,
    )

    # Use empty scanned_at in CSV so it matches the DB value of None.
    importer = _make_importer(tmp_path, [_sign_row("UNC", scanned_at="")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    assert summary["signs_updated"] == 0
    result = summary["phase_results"]["signs"]["update"]
    assert result["skipped"] >= 1


@pytest.mark.django_db
def test_update_signs_force_update_bypasses_comparison(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """With force_update=True, even unchanged records are updated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="FU1",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        direction=None,
        height=250,
        scanned_at=None,
        attachment_url="",
        txt=None,
        value=None,
        condition=None,
        location_specifier=None,
        mount_real=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("FU1", scanned_at="")], force_update=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    assert summary["signs_updated"] == 1


@pytest.mark.django_db
def test_update_signs_skips_invalid_coordinates(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A CSV row with invalid coordinates is skipped during update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="BDU",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("BDU", x="NOT_NUM", y="BAD")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    assert summary["signs_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "BDU" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_signs_skips_unknown_device_type_code(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A sign update row with an unknown code is skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="UKC",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("UKC", code="NOTEXIST")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    assert summary["signs_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "UKC" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_signs_ignores_rows_not_in_db(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows in the CSV that do not exist in the DB are ignored by the update phase.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("NONEX")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    assert summary["signs_updated"] == 0


@pytest.mark.django_db
def test_update_signs_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, existing signs are not modified in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="DRYU",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DRYU")], dry_run=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DRYU")
    # Location not written in dry-run
    assert sign.location.x == pytest.approx(25497100.0, abs=1)
    assert summary["signs_updated"] == 1


@pytest.mark.django_db
def test_update_signs_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_update_signs writes a phase_results entry for ('signs', 'update').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="PH2",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("PH2")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signs(summary)

    result = summary.get("phase_results", {}).get("signs", {}).get("update")
    assert result is not None
    assert result["updated"] == 1
    assert "skipped" in result


# ===========================================================================
# _deactivate_signs — deactivation
# ===========================================================================


@pytest.mark.django_db
def test_deactivate_signs_sets_lifecycle_inactive(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets lifecycle to INACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="DEA1",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DEA1", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DEA1")
    assert sign.lifecycle == Lifecycle.INACTIVE


@pytest.mark.django_db
def test_deactivate_signs_sets_validity_period_end(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets validity_period_end to today.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="DEA2",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DEA2", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DEA2")
    assert sign.validity_period_end == datetime.date(2023, 8, 15)


@pytest.mark.django_db
def test_deactivate_signs_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets updated_at on the record.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="DEA3",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DEA3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DEA3")
    assert sign.updated_at is not None


@pytest.mark.django_db
def test_deactivate_signs_updates_source_name(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation stamps source_name to StreetScan2025.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    # Use V1 source_name prefix so the DB builder picks up this sign,
    # then verify deactivation stamps it to the V2 value.
    TrafficSignRealFactory(
        source_id="DEA4",
        source_name="StreetScan",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DEA4", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DEA4")
    assert sign.source_name == "StreetScan2025"


@pytest.mark.django_db
def test_deactivate_signs_skips_non_removed_rows(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Non-Removed rows are not deactivated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="NRM1",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("NRM1", status="Changed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="NRM1")
    assert sign.lifecycle == Lifecycle.ACTIVE
    assert summary["signs_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_signs_skips_rows_not_in_db(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Removed rows that do not exist in the DB are silently skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("GHOST", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    assert summary["signs_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_signs_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, signs are not deactivated in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="DRYD",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("DRYD", status="Removed")], dry_run=True, phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    sign = TrafficSignReal.objects.get(source_id="DRYD")
    assert sign.lifecycle == Lifecycle.ACTIVE
    assert summary["signs_deactivated"] == 1


@pytest.mark.django_db
def test_deactivate_signs_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_deactivate_signs writes a phase_results entry for ('signs', 'deactivate').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    TrafficSignRealFactory(
        source_id="PH3",
        source_name="StreetScan2025",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("PH3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signs(summary)

    result = summary.get("phase_results", {}).get("signs", {}).get("deactivate")
    assert result is not None
    assert result["deactivated"] == 1
