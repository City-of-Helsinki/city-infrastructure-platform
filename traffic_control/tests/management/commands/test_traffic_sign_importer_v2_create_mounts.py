"""Tests for TrafficSignImporterV2._create_mounts and _get_mounts."""
from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_import import TrafficSignImporterV2
from traffic_control.models import MountReal
from traffic_control.tests.factories import MountRealFactory, MountTypeFactory, OwnerFactory

# ---------------------------------------------------------------------------
# CSV helpers (reuse the same column layout as the analyzer tests)
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

# Valid Helsinki-area EPSG:3879 coordinates
_COORDS = ["25497188.0", "6673461.0", "8.0", "0.01", "0.01", "0.01"]
_TS = "2023/08/15 12:00:00+00"


def _mount_row(obj_id: str, status: str = "New", x: str = _COORDS[0], y: str = _COORDS[1]) -> list[str]:
    """Build a mount CSV row.

    Args:
        obj_id (str): Object identifier used as source_id.
        status (str): CSV status field value.
        x (str): X coordinate.
        y (str): Y coordinate.

    Returns:
        list[str]: Field values for one mount row.
    """
    return ["1", obj_id, x, y, _COORDS[2], _COORDS[3], _COORDS[4], _COORDS[5], status, _TS, ""]


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
    object_types: list[str] | None = None,
    phases: list[str] | None = None,
) -> TrafficSignImporterV2:
    """Build a TrafficSignImporterV2 with given mount rows and an empty sign file.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.
        mount_rows (list[list[str]]): Mount CSV data rows.
        dry_run (bool): Whether to enable dry-run mode.
        object_types (list[str] | None): Object types to pass; defaults to ["mounts"].
        phases (list[str] | None): Phases to pass; defaults to ["create"].

    Returns:
        TrafficSignImporterV2: Configured importer instance.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, mount_rows)
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [])
    return TrafficSignImporterV2(
        mount_file=mf,
        sign_file=sf,
        object_types=object_types or ["mounts"],
        phases=phases or ["create"],
        dry_run=dry_run,
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
# TrafficSignImporterV2.__init__ — owner lookup failures
# ===========================================================================

_LOAD_OWNERS_PATH = (
    "traffic_control.analyze_utils.traffic_sign_data_v2_import.TrafficSignImporterV2._load_required_owners"
)


@pytest.mark.django_db
def test_init_raises_when_default_owner_missing(tmp_path: Path) -> None:
    """RuntimeError is raised immediately when 'Helsingin kaupunki' owner is absent.

    Uses mock.patch to simulate the owner being missing without touching the DB,
    since migration 0022_initial_owners seeds both owners in the test database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, [])
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [])
    with patch(_LOAD_OWNERS_PATH, side_effect=RuntimeError("Required Owner 'Helsingin kaupunki' not found")):
        with pytest.raises(RuntimeError, match="Helsingin kaupunki"):
            TrafficSignImporterV2(
                mount_file=mf,
                sign_file=sf,
                object_types=["mounts"],
                phases=["create"],
            )


@pytest.mark.django_db
def test_init_raises_when_private_owner_missing(tmp_path: Path) -> None:
    """RuntimeError is raised immediately when 'Yksityinen' owner is absent.

    Uses mock.patch to simulate the owner being missing without touching the DB,
    since migration 0022_initial_owners seeds both owners in the test database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mf = _write_csv(tmp_path, _MOUNT_CSV_HEADER, [])
    sf = _write_csv(tmp_path, _SIGN_CSV_HEADER, [])
    with patch(_LOAD_OWNERS_PATH, side_effect=RuntimeError("Required Owner 'Yksityinen' not found")):
        with pytest.raises(RuntimeError, match="Yksityinen"):
            TrafficSignImporterV2(
                mount_file=mf,
                sign_file=sf,
                object_types=["mounts"],
                phases=["create"],
            )


# ===========================================================================
# _create_mounts — basic creation
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_inserts_new_records(tmp_path: Path, default_owner, mount_type) -> None:
    """New mount rows are inserted into the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("M1"), _mount_row("M2")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert MountReal.objects.filter(source_id__in=["M1", "M2"], source_name="StreetScan2025").count() == 2


@pytest.mark.django_db
def test_create_mounts_sets_source_name(tmp_path: Path, default_owner, mount_type) -> None:
    """Created mounts always have source_name='StreetScan2025'.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("M10")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    mount = MountReal.objects.get(source_id="M10")
    assert mount.source_name == "StreetScan2025"


@pytest.mark.django_db
def test_create_mounts_sets_owner(tmp_path: Path, default_owner, mount_type) -> None:
    """Created mounts have the default owner set.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("M20")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    mount = MountReal.objects.get(source_id="M20")
    assert mount.owner == default_owner


@pytest.mark.django_db
def test_create_mounts_sets_scanned_at(tmp_path: Path, default_owner, mount_type) -> None:
    """Created mounts have scanned_at parsed from the CSV timestamp.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("M30")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    mount = MountReal.objects.get(source_id="M30")
    assert mount.scanned_at is not None
    assert mount.scanned_at.year == 2023


# ===========================================================================
# _create_mounts — idempotency: existing source_ids are skipped
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_skips_existing_source_ids(tmp_path: Path, default_owner, mount_type) -> None:
    """A row whose source_id already exists in the DB is not inserted again.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(source_id="EXISTING", source_name="StreetScan2025", owner=default_owner)

    importer = _make_importer(tmp_path, [_mount_row("EXISTING"), _mount_row("NEW")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert MountReal.objects.filter(source_id="EXISTING").count() == 1  # no duplicate
    assert MountReal.objects.filter(source_id="NEW").count() == 1


@pytest.mark.django_db
def test_create_mounts_count_reflects_only_new_records(tmp_path: Path, default_owner, mount_type) -> None:
    """summary['mounts_created'] counts only newly inserted records.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    MountRealFactory(source_id="OLD", source_name="StreetScan2025", owner=default_owner)

    importer = _make_importer(tmp_path, [_mount_row("OLD"), _mount_row("NEW1"), _mount_row("NEW2")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert summary["mounts_created"] == 2


# ===========================================================================
# _create_mounts — geometry validation
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_skips_row_with_invalid_coordinates(tmp_path: Path, default_owner) -> None:
    """A row with non-numeric coordinates is skipped and a skip entry is logged.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
    """
    bad_row = _mount_row("BAD_COORDS", x="NOT_A_NUMBER", y="ALSO_BAD")
    importer = _make_importer(tmp_path, [bad_row])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert MountReal.objects.filter(source_id="BAD_COORDS").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "BAD_COORDS" and e["level"] == "skip"]
    assert len(skips) == 1


@pytest.mark.django_db
def test_create_mounts_skips_row_with_zero_coordinates(tmp_path: Path, default_owner) -> None:
    """A row with (0, 0) coordinates fails geometry_is_legit and is skipped.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
    """
    zero_row = _mount_row("ZERO_COORDS", x="0.0", y="0.0")
    importer = _make_importer(tmp_path, [zero_row])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert MountReal.objects.filter(source_id="ZERO_COORDS").count() == 0
    skips = [e for e in summary["details"] if e["source_id"] == "ZERO_COORDS" and e["level"] == "skip"]
    assert len(skips) == 1


# ===========================================================================
# _create_mounts — phase result recording
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_records_phase_result(tmp_path: Path, default_owner, mount_type) -> None:
    """_create_mounts writes a phase_results entry for ('mounts', 'create').

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("PR1"), _mount_row("PR2")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    result = summary.get("phase_results", {}).get("mounts", {}).get("create")
    assert result is not None
    assert result["created"] == 2
    assert "skipped" in result


@pytest.mark.django_db
def test_create_mounts_phase_result_skipped_count_matches_details(tmp_path: Path, default_owner) -> None:
    """The skipped count in phase_results equals the number of skip entries in details.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
    """
    bad_row = _mount_row("SKIP_ME", x="0.0", y="0.0")
    importer = _make_importer(tmp_path, [bad_row])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    result = summary["phase_results"]["mounts"]["create"]
    detail_skips = len([e for e in summary["details"] if e["level"] == "skip"])
    assert result["skipped"] == detail_skips


# ===========================================================================
# _create_mounts — dry run
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_dry_run_does_not_write_to_db(tmp_path: Path, default_owner, mount_type) -> None:
    """In dry-run mode, no MountReal records are created in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("DRY1"), _mount_row("DRY2")], dry_run=True)
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert MountReal.objects.filter(source_id__in=["DRY1", "DRY2"]).count() == 0


@pytest.mark.django_db
def test_create_mounts_dry_run_still_counts_created(tmp_path: Path, default_owner, mount_type) -> None:
    """In dry-run mode, summary['mounts_created'] still reflects what would be created.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("DRY3"), _mount_row("DRY4")], dry_run=True)
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert summary["mounts_created"] == 2


# ===========================================================================
# _create_mounts — processed_mount_source_ids tracking
# ===========================================================================


@pytest.mark.django_db
def test_create_mounts_populates_processed_source_ids(tmp_path: Path, default_owner, mount_type) -> None:
    """Successfully generated mount source_ids appear in processed_mount_source_ids.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
        mount_type: MountType fixture.
    """
    importer = _make_importer(tmp_path, [_mount_row("PROC1"), _mount_row("PROC2")])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert "PROC1" in summary.get("processed_mount_source_ids", [])
    assert "PROC2" in summary.get("processed_mount_source_ids", [])


@pytest.mark.django_db
def test_create_mounts_skipped_rows_not_in_processed(tmp_path: Path, default_owner) -> None:
    """Rows skipped due to invalid geometry are not in processed_mount_source_ids.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        default_owner: Owner fixture.
    """
    bad_row = _mount_row("SKIP_PROC", x="0.0", y="0.0")
    importer = _make_importer(tmp_path, [bad_row])
    summary: dict = {"details": []}
    importer._create_mounts(summary)

    assert "SKIP_PROC" not in summary.get("processed_mount_source_ids", [])
