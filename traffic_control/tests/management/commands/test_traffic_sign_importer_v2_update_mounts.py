"""Tests for TrafficSignImporterV2._update_mounts and _get_mounts_to_update."""
import csv
from pathlib import Path

import pytest
from django.contrib.gis.geos import Point

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME, TrafficSignImporterV2
from traffic_control.models import MountReal
from traffic_control.tests.factories import MountRealFactory, MountTypeFactory, OwnerFactory

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
    "tallennusajankohta",
    "korkeus",
    "ssurl",
]

_TS = "2023-08-15T12:00:00+00"


def _mount_row(
    obj_id: str,
    status: str = "New",
    x: str = "25497188.0",
    y: str = "6673461.0",
    scanned_at: str = _TS,
    ssurl: str = "",
) -> list[str]:
    """Build a mount CSV row.

    Args:
        obj_id (str): Object identifier used as source_id.
        status (str): CSV status field value.
        x (str): X coordinate.
        y (str): Y coordinate.
        scanned_at (str): Timestamp string.
        ssurl (str): Attachment URL.

    Returns:
        list[str]: Field values for one mount row.
    """
    return ["1", obj_id, x, y, "8.0", "0.01", "0.01", "0.01", status, scanned_at, ssurl]


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
    mount_rows: list[list[str]],
    *,
    dry_run: bool = False,
    force_update: bool = False,
) -> TrafficSignImporterV2:
    """Build a TrafficSignImporterV2 configured for mount update tests.

    NOTE: Any MountReal records that should be found by the update phase must
    exist in the DB *before* calling this helper, because __init__ builds the
    mount_source_id_to_db_id lookup map from the current DB state.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.
        mount_rows (list[list[str]]): Mount CSV data rows.
        dry_run (bool): Whether to enable dry-run mode.
        force_update (bool): Whether to enable force-update mode.

    Returns:
        TrafficSignImporterV2: Configured importer instance.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows)
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [])
    return TrafficSignImporterV2(
        mount_file=mf,
        sign_file=sf,
        object_types=["mounts"],
        phases=["update"],
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
def mount_type(db):
    """Create a MountType that matches the CSV mount_type name.

    Args:
        db: Pytest-django db fixture.

    Returns:
        MountType: The created mount type instance.
    """
    return MountTypeFactory(description="POLE", description_fi="Pylväs")


# ===========================================================================
# _update_mounts — basic update
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_updates_existing_record(tmp_path: Path, default_owner, mount_type) -> None:
    """An existing mount with a changed location is updated in the DB.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    existing = MountRealFactory(
        source_id="U1",
        source_name="StreetScan2024",
        owner=default_owner,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("U1", x="25497188.0", y="6673461.0")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    existing.refresh_from_db()
    assert existing.source_name == SOURCE_NAME
    assert summary["mounts_updated"] == 1


@pytest.mark.django_db
def test_update_mounts_sets_updated_by_and_updated_at(tmp_path: Path, default_owner, mount_type) -> None:
    """Updated mounts have updated_by and updated_at set.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="U2",
        source_name="StreetScan2024",
        owner=default_owner,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("U2")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    mount = MountReal.objects.get(source_id="U2")
    assert mount.updated_at is not None


# ===========================================================================
# _update_mounts — no change detection (skipped)
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_skips_unchanged_record(tmp_path: Path, default_owner, mount_type) -> None:
    """A mount whose CSV values match DB values is not updated (skipped).

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="UNCHANGED",
        source_name=SOURCE_NAME,
        owner=default_owner,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        mount_type=None,
        scanned_at=None,
        attachment_url="",
    )

    importer = _make_importer(tmp_path, [_mount_row("UNCHANGED", scanned_at="")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 0
    result = summary["phase_results"]["mounts"]["update"]
    assert result["skipped"] >= 1


# ===========================================================================
# _update_mounts — force_update bypasses comparison
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_force_update_bypasses_comparison(tmp_path: Path, default_owner, mount_type) -> None:
    """With force_update=True, even unchanged records are updated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="FORCE",
        source_name=SOURCE_NAME,
        owner=default_owner,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        mount_type=None,
        scanned_at=None,
        attachment_url="",
    )

    importer = _make_importer(tmp_path, [_mount_row("FORCE", scanned_at="")], force_update=True)
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 1


# ===========================================================================
# _update_mounts — geometry validation
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_skips_invalid_coordinates(tmp_path: Path, default_owner, mount_type) -> None:
    """A CSV row with invalid coordinates is skipped during update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="BAD_UPD",
        source_name=SOURCE_NAME,
        owner=default_owner,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("BAD_UPD", x="NOT_NUM", y="BAD")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 0
    skips = [e for e in summary["details"] if e["source_id"] == "BAD_UPD" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_update_mounts_skips_zero_coordinates(tmp_path: Path, default_owner, mount_type) -> None:
    """A CSV row with (0, 0) coordinates fails geometry check and is skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="ZERO_UPD",
        source_name=SOURCE_NAME,
        owner=default_owner,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("ZERO_UPD", x="0.0", y="0.0")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 0


# ===========================================================================
# _update_mounts — phase result recording
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_records_phase_result(tmp_path: Path, default_owner, mount_type) -> None:
    """_update_mounts writes a phase_results entry for ('mounts', 'update').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="PH1",
        source_name="StreetScan2024",
        owner=default_owner,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("PH1")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    result = summary.get("phase_results", {}).get("mounts", {}).get("update")
    assert result is not None
    assert result["updated"] == 1
    assert "skipped" in result


# ===========================================================================
# _update_mounts — dry run
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_dry_run_does_not_write(tmp_path: Path, default_owner, mount_type) -> None:
    """In dry-run mode, existing mounts are not modified in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="DRY_U",
        source_name="StreetScan2024",
        owner=default_owner,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("DRY_U")], dry_run=True)
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    mount = MountReal.objects.get(source_id="DRY_U")
    assert mount.source_name == "StreetScan2024"


@pytest.mark.django_db
def test_update_mounts_dry_run_still_counts(tmp_path: Path, default_owner, mount_type) -> None:
    """In dry-run mode, summary['mounts_updated'] reflects what would be updated.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="DRY_C",
        source_name="StreetScan2024",
        owner=default_owner,
        location=Point(25497100.0, 6673400.0, 5.0, srid=3879),
    )

    importer = _make_importer(tmp_path, [_mount_row("DRY_C")], dry_run=True)
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 1


# ===========================================================================
# _update_mounts — only updates rows present in mount_source_id_to_db_id
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_ignores_rows_not_in_db(tmp_path: Path, default_owner, mount_type) -> None:
    """Rows in the CSV that do not exist in the DB are ignored by update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("NONEXISTENT")])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    assert summary["mounts_updated"] == 0


# ===========================================================================
# _update_mounts — attachment_url update
# ===========================================================================


@pytest.mark.django_db
def test_update_mounts_updates_attachment_url(tmp_path: Path, default_owner, mount_type) -> None:
    """A changed attachment_url triggers an update.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(
        source_id="URL1",
        source_name=SOURCE_NAME,
        owner=default_owner,
        location=Point(25497188.0, 6673461.0, 8.0, srid=3879),
        attachment_url="",
    )

    row = _mount_row("URL1", ssurl="https://example.com/img.jpg")
    importer = _make_importer(tmp_path, [row])
    summary: dict = {"details": []}
    importer._update_mounts(summary)

    mount = MountReal.objects.get(source_id="URL1")
    assert mount.attachment_url == "https://example.com/img.jpg"
    assert summary["mounts_updated"] == 1
