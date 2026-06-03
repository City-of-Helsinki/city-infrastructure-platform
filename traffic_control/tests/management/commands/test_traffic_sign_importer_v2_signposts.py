"""Tests for TrafficSignImporterV2 signpost phases: create, update, deactivate."""
import csv
import datetime
from pathlib import Path

import pytest
from django.contrib.gis.geos import Point

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME, TrafficSignImporterV2
from traffic_control.enums import Lifecycle
from traffic_control.models import SignpostReal
from traffic_control.tests.factories import (
    MountTypeFactory,
    OwnerFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
)

# ---------------------------------------------------------------------------
# CSV helpers  (same layout as the sign tests)
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
# Signpost codes start with 6, 7, G or F — use a plain '6xx' code.
_SIGNPOST_CODE = "645"


def _sign_row(
    obj_id: str,
    code: str = _SIGNPOST_CODE,
    status: str = "New",
    x: str = _COORDS[0],
    y: str = _COORDS[1],
    mount_id: str = "",
    parent_sign_id: str = "",
    txt: str = "",
    scanned_at: str = _TS,
    ssurl: str = "",
) -> list[str]:
    """Build a sign CSV row for a signpost.

    Args:
        obj_id (str): Source identifier.
        code (str): Device type code (merkkikoodi); must start with 6/7/G/F.
        status (str): CSV status field.
        x (str): X coordinate (EPSG:3879).
        y (str): Y coordinate (EPSG:3879).
        mount_id (str): kiinnityskohta_id value.
        parent_sign_id (str): lisäkilven_päämerkin_id value (parent signpost).
        txt (str): teksti value.
        scanned_at (str): recordedat timestamp.
        ssurl (str): Attachment URL.

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
    """Build a TrafficSignImporterV2 configured for signpost tests.

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
        object_types=["signposts"],
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
    """Create a TrafficControlDeviceType matching the signpost code.

    Args:
        db: Pytest-django db fixture.

    Returns:
        TrafficControlDeviceType: The created device type instance.
    """
    return TrafficControlDeviceTypeFactory(code=_SIGNPOST_CODE)


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
# _create_signposts
# ===========================================================================


@pytest.mark.django_db
def test_create_signposts_inserts_new_records(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """New signpost rows are inserted into the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SP1"), _sign_row("SP2")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id__in=["SP1", "SP2"], source_name=SOURCE_NAME).count() == 2


@pytest.mark.django_db
def test_create_signposts_sets_lifecycle_active(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Created signposts have lifecycle set to ACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPLC")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPLC")
    assert sp.lifecycle == Lifecycle.ACTIVE


@pytest.mark.django_db
def test_create_signposts_skips_removed_status(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows with status='Removed' are not inserted.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPRM", status="Removed")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPRM").count() == 0
    assert summary["signposts_created"] == 0


@pytest.mark.django_db
def test_create_signposts_skips_invalid_coordinates(tmp_path: Path, default_owner, device_type) -> None:
    """Rows with non-numeric coordinates are skipped with a skip detail entry.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPBD", x="NOT_NUM", y="BAD")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPBD").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "SPBD" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_signposts_skips_zero_coordinates(tmp_path: Path, default_owner, device_type) -> None:
    """Rows with (0, 0) coordinates fail the geometry check and are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPZERO", x="0.0", y="0.0")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPZERO").count() == 0


@pytest.mark.django_db
def test_create_signposts_skips_unknown_device_type_code(tmp_path: Path, default_owner, mount_type) -> None:
    """Rows whose device type code is not in the DB are skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPUNK", code="6DOESNOTEXIST")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPUNK").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "SPUNK" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_signposts_skips_already_existing_source_ids(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """Rows whose source_id already exists in the DB are not inserted again.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPEXIST",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
    )

    importer = _make_importer(tmp_path, [_sign_row("SPEXIST"), _sign_row("SPNEW")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPEXIST").count() == 1
    assert SignpostReal.objects.filter(source_id="SPNEW").count() == 1


@pytest.mark.django_db
def test_create_signposts_warning_for_unresolved_mount(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A signpost referencing a non-existent mount is imported with a warning.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPWM", mount_id="NONEXISTENT_MOUNT")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPWM").count() == 1
    warnings = [e for e in summary["details"] if e["source_id"] == "SPWM" and e["level"] == "warning"]
    assert any("Mount not found" in w["reason"] for w in warnings)


@pytest.mark.django_db
def test_create_signposts_child_links_to_parent_created_same_run(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A child signpost is linked to a root signpost created in the same run (pass-2).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(
        tmp_path,
        [_sign_row("SPROOT"), _sign_row("SPCHILD", parent_sign_id="SPROOT")],
    )
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert summary["signposts_created"] == 2
    child = SignpostReal.objects.get(source_id="SPCHILD")
    parent = SignpostReal.objects.get(source_id="SPROOT")
    assert child.parent_id == parent.pk


@pytest.mark.django_db
def test_create_signposts_child_links_to_parent_already_in_db(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A child signpost is linked to a parent that already existed in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    existing_parent = SignpostRealFactory(
        source_id="SPPARENT_DB",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
    )

    importer = _make_importer(tmp_path, [_sign_row("SPKID", parent_sign_id="SPPARENT_DB")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    child = SignpostReal.objects.get(source_id="SPKID")
    assert child.parent_id == existing_parent.pk


@pytest.mark.django_db
def test_create_signposts_warning_for_unresolved_parent(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A signpost with an unknown parent_sign_id is imported with a warning.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPNOP", parent_sign_id="MISSING_PARENT")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPNOP").count() == 1
    sp = SignpostReal.objects.get(source_id="SPNOP")
    assert sp.parent_id is None
    warnings = [e for e in summary["details"] if e["source_id"] == "SPNOP" and e["level"] == "warning"]
    assert any("Parent signpost not found" in w["reason"] for w in warnings)


@pytest.mark.django_db
def test_create_signposts_three_level_tree(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Multi-pass handles three-level tree: Grandparent → Parent → Child.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(
        tmp_path,
        [
            _sign_row("SPGP"),
            _sign_row("SPP", parent_sign_id="SPGP"),
            _sign_row("SPC", parent_sign_id="SPP"),
        ],
    )
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert summary["signposts_created"] == 3
    grandparent = SignpostReal.objects.get(source_id="SPGP")
    parent = SignpostReal.objects.get(source_id="SPP")
    child = SignpostReal.objects.get(source_id="SPC")

    assert grandparent.parent_id is None
    assert parent.parent_id == grandparent.pk
    assert child.parent_id == parent.pk


@pytest.mark.django_db
def test_create_signposts_four_level_tree(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Multi-pass handles four-level tree: Grandparent → Parent → Node → Leaf.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(
        tmp_path,
        [
            _sign_row("SPGGP"),
            _sign_row("SPGP2", parent_sign_id="SPGGP"),
            _sign_row("SPP2", parent_sign_id="SPGP2"),
            _sign_row("SPL", parent_sign_id="SPP2"),
        ],
    )
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert summary["signposts_created"] == 4
    great_grandparent = SignpostReal.objects.get(source_id="SPGGP")
    grandparent = SignpostReal.objects.get(source_id="SPGP2")
    parent = SignpostReal.objects.get(source_id="SPP2")
    leaf = SignpostReal.objects.get(source_id="SPL")

    assert great_grandparent.parent_id is None
    assert grandparent.parent_id == great_grandparent.pk
    assert parent.parent_id == grandparent.pk
    assert leaf.parent_id == parent.pk


@pytest.mark.django_db
def test_create_signposts_multiple_branches(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Multi-pass handles multiple independent branches at different depths.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(
        tmp_path,
        [
            # Branch 1: 3 levels
            _sign_row("SPB1R"),
            _sign_row("SPB1C1", parent_sign_id="SPB1R"),
            _sign_row("SPB1C2", parent_sign_id="SPB1C1"),
            # Branch 2: 2 levels
            _sign_row("SPB2R"),
            _sign_row("SPB2C", parent_sign_id="SPB2R"),
            # Orphan
            _sign_row("SPORP"),
        ],
    )
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert summary["signposts_created"] == 6

    # Branch 1
    b1_root = SignpostReal.objects.get(source_id="SPB1R")
    b1_child1 = SignpostReal.objects.get(source_id="SPB1C1")
    b1_child2 = SignpostReal.objects.get(source_id="SPB1C2")
    assert b1_root.parent_id is None
    assert b1_child1.parent_id == b1_root.pk
    assert b1_child2.parent_id == b1_child1.pk

    # Branch 2
    b2_root = SignpostReal.objects.get(source_id="SPB2R")
    b2_child = SignpostReal.objects.get(source_id="SPB2C")
    assert b2_root.parent_id is None
    assert b2_child.parent_id == b2_root.pk

    # Orphan
    orphan = SignpostReal.objects.get(source_id="SPORP")
    assert orphan.parent_id is None


@pytest.mark.django_db
def test_create_signposts_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_create_signposts writes a phase_results entry for ('signposts', 'create').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPPR1"), _sign_row("SPPR2")])
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    result = summary.get("phase_results", {}).get("signposts", {}).get("create")
    assert result is not None
    assert result["created"] == 2


@pytest.mark.django_db
def test_create_signposts_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode no SignpostReal records are written but count reflects candidates.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPDRY")], dry_run=True)
    summary: dict = {"details": []}
    importer._create_signposts(summary)

    assert SignpostReal.objects.filter(source_id="SPDRY").count() == 0
    assert summary["signposts_created"] == 1


# ===========================================================================
# _update_signposts
# ===========================================================================


@pytest.mark.django_db
def test_update_signposts_updates_existing_record(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """An existing signpost with a different location is updated in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPU1",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPU1")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPU1")
    assert sp.location.x == pytest.approx(25497188.0, abs=1)
    assert summary["signposts_updated"] == 1


@pytest.mark.django_db
def test_update_signposts_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Updated signposts have updated_at populated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPUA",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPUA")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPUA")
    assert sp.updated_at is not None


@pytest.mark.django_db
def test_update_signposts_skips_unchanged_record(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A signpost whose CSV values match DB values is skipped (not re-written).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPUNC",
        source_name=SOURCE_NAME,
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

    importer = _make_importer(tmp_path, [_sign_row("SPUNC", scanned_at="")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 0
    result = summary["phase_results"]["signposts"]["update"]
    assert result["skipped"] >= 1


@pytest.mark.django_db
def test_update_signposts_force_update_bypasses_comparison(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """With force_update=True, even unchanged signposts are re-written.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPFU",
        source_name=SOURCE_NAME,
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
        mount_type=None,
    )

    importer = _make_importer(tmp_path, [_sign_row("SPFU", scanned_at="")], force_update=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 1


@pytest.mark.django_db
def test_update_signposts_skips_removed_rows(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Rows with status='Removed' are not touched by the update phase.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPURM",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPURM", status="Removed")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 0


@pytest.mark.django_db
def test_update_signposts_skips_invalid_coordinates(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """A CSV row with invalid coordinates is skipped during the update phase.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPBDU",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPBDU", x="NOT_NUM", y="BAD")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "SPBDU" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_signposts_skips_unknown_device_type_code(
    tmp_path: Path, default_owner, device_type, mount_type
) -> None:
    """A signpost update row with an unknown code is skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPUKC",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPUKC", code="6NOTEXIST")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "SPUKC" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_signposts_ignores_rows_not_in_db(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """CSV rows that have no matching DB record are silently ignored by update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPNONEX")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    assert summary["signposts_updated"] == 0


@pytest.mark.django_db
def test_update_signposts_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, existing signposts are not modified in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDRYU",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDRYU")], dry_run=True, phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDRYU")
    assert sp.location.x == pytest.approx(25497100.0, abs=1)
    assert summary["signposts_updated"] == 1


@pytest.mark.django_db
def test_update_signposts_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_update_signposts writes a phase_results entry for ('signposts', 'update').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPPH2",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPPH2")], phases=["update"])
    summary: dict = {"details": []}
    importer._update_signposts(summary)

    result = summary.get("phase_results", {}).get("signposts", {}).get("update")
    assert result is not None
    assert result["updated"] == 1
    assert "skipped" in result


# ===========================================================================
# _deactivate_signposts
# ===========================================================================


@pytest.mark.django_db
def test_deactivate_signposts_sets_lifecycle_inactive(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets lifecycle to INACTIVE.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDEA1",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDEA1", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDEA1")
    assert sp.lifecycle == Lifecycle.INACTIVE


@pytest.mark.django_db
def test_deactivate_signposts_sets_validity_period_end(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets validity_period_end to today.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDEA2",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDEA2", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDEA2")
    assert sp.validity_period_end == datetime.date(2023, 8, 15)


@pytest.mark.django_db
def test_deactivate_signposts_sets_updated_at(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation populates updated_at on the record.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDEA3",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDEA3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDEA3")
    assert sp.updated_at is not None


@pytest.mark.django_db
def test_deactivate_signposts_stamps_source_name(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Deactivation sets source_name to SOURCE_NAME.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDEA4",
        source_name="StreetScan",
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDEA4", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDEA4")
    assert sp.source_name == SOURCE_NAME


@pytest.mark.django_db
def test_deactivate_signposts_skips_non_removed_rows(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Non-Removed rows are not deactivated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPNRM",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPNRM", status="Changed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPNRM")
    assert sp.lifecycle == Lifecycle.ACTIVE
    assert summary["signposts_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_signposts_skips_rows_not_in_db(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """Removed rows with no matching DB record are silently skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_sign_row("SPGHOST", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    assert summary["signposts_deactivated"] == 0


@pytest.mark.django_db
def test_deactivate_signposts_dry_run_does_not_write(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """In dry-run mode, signposts are not deactivated in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPDRYD",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPDRYD", status="Removed")], dry_run=True, phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    sp = SignpostReal.objects.get(source_id="SPDRYD")
    assert sp.lifecycle == Lifecycle.ACTIVE
    assert summary["signposts_deactivated"] == 1


@pytest.mark.django_db
def test_deactivate_signposts_phase_result_recorded(tmp_path: Path, default_owner, device_type, mount_type) -> None:
    """_deactivate_signposts writes a phase_results entry for ('signposts', 'deactivate').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        device_type: DeviceType fixture.
        mount_type: MountType fixture.
    """
    SignpostRealFactory(
        source_id="SPPH3",
        source_name=SOURCE_NAME,
        owner=default_owner,
        device_type=device_type,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_sign_row("SPPH3", status="Removed")], phases=["deactivate"])
    summary: dict = {"details": []}
    importer._deactivate_signposts(summary)

    result = summary.get("phase_results", {}).get("signposts", {}).get("deactivate")
    assert result is not None
    assert result["deactivated"] == 1
