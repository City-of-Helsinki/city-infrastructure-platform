"""End-to-end tests for the import_streetscan_signs_v2 management command."""
import csv
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOUNT_CSV_HEADER = ["OBJECTID", "id", "x", "y", "z", "stdx", "stdy", "stdz", "status", "tallennusajankohta", "ssurl"]
_SIGN_CSV_HEADER = [
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


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> str:
    """Write a minimal CSV file and return its path as a string.

    Args:
        path (Path): Directory to write the file into.
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


def _make_csv_files(tmp_path: Path) -> tuple[str, str]:
    """Create minimal empty mount and sign CSV files.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.

    Returns:
        tuple[str, str]: Paths to (mount_file, sign_file).
    """
    return (
        _write_csv(tmp_path, _MOUNT_CSV_HEADER, []),
        _write_csv(tmp_path, _SIGN_CSV_HEADER, []),
    )


def _call(mount_file: str, sign_file: str, **kwargs) -> tuple[str, str]:
    """Call the management command and capture stdout/stderr.

    Args:
        mount_file (str): Path to mount CSV.
        sign_file (str): Path to sign CSV.
        **kwargs: Additional keyword arguments forwarded to call_command.

    Returns:
        tuple[str, str]: (stdout output, stderr output).
    """
    stdout = StringIO()
    stderr = StringIO()
    call_command(
        "import_streetscan_signs_v2",
        mount_file=mount_file,
        sign_file=sign_file,
        stdout=stdout,
        stderr=stderr,
        **kwargs,
    )
    return stdout.getvalue(), stderr.getvalue()


# ===========================================================================
# Missing file validation
# ===========================================================================


@pytest.mark.django_db
def test_missing_mount_file_prints_error(tmp_path: Path) -> None:
    """Command prints an error to stderr when --mount-file does not exist.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    _, sign_file = _make_csv_files(tmp_path)
    stdout, stderr = _call("/nonexistent/mounts.csv", sign_file)
    assert "Mount file not found" in stderr
    assert stdout == ""


@pytest.mark.django_db
def test_missing_sign_file_prints_error(tmp_path: Path) -> None:
    """Command prints an error to stderr when --sign-file does not exist.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, _ = _make_csv_files(tmp_path)
    stdout, stderr = _call(mount_file, "/nonexistent/signs.csv")
    assert "Sign file not found" in stderr
    assert stdout == ""


@pytest.mark.django_db
def test_both_files_missing_reports_mount_error_first(tmp_path: Path) -> None:
    """When both files are missing the mount-file error is reported first.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    _, stderr = _call("/bad/mounts.csv", "/bad/signs.csv")
    assert "Mount file not found" in stderr


# ===========================================================================
# Smoke tests — real importer with empty CSV files
# ===========================================================================


@pytest.mark.django_db
def test_command_completes_with_empty_csv_files(tmp_path: Path) -> None:
    """Command runs to completion and prints a summary when both CSVs are empty.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    stdout, stderr = _call(mount_file, sign_file)
    assert "Import summary" in stdout
    assert stderr == ""


@pytest.mark.django_db
def test_dry_run_flag_noted_in_output(tmp_path: Path) -> None:
    """Running with --dry-run prints a DRY RUN notice to stdout.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    stdout, _ = _call(mount_file, sign_file, dry_run=True)
    assert "DRY RUN" in stdout


@pytest.mark.django_db
def test_force_update_flag_noted_in_output(tmp_path: Path) -> None:
    """Running with --force-update prints a FORCE UPDATE notice to stdout.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    stdout, _ = _call(mount_file, sign_file, force_update=True)
    assert "FORCE UPDATE" in stdout


@pytest.mark.django_db
def test_dry_run_writes_no_db_records(tmp_path: Path) -> None:
    """Running with --dry-run creates no records in the database.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    from traffic_control.models import MountReal, TrafficSignReal

    mount_file, sign_file = _make_csv_files(tmp_path)
    _call(mount_file, sign_file, dry_run=True)

    assert MountReal.objects.filter(source_name=SOURCE_NAME).count() == 0
    assert TrafficSignReal.objects.filter(source_name=SOURCE_NAME).count() == 0


@pytest.mark.django_db
def test_run_log_row_is_created(tmp_path: Path) -> None:
    """A StreetScanImportRun row is written to the DB after a successful run.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    from traffic_control.models.streetscan_import import StreetScanImportRun

    mount_file, sign_file = _make_csv_files(tmp_path)
    _call(mount_file, sign_file)

    assert StreetScanImportRun.objects.filter(mount_file=mount_file, sign_file=sign_file).exists()


@pytest.mark.django_db
def test_dry_run_log_row_marked_as_dry_run(tmp_path: Path) -> None:
    """The run log row created for a dry run has is_dry_run=True.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    from traffic_control.models.streetscan_import import StreetScanImportRun

    mount_file, sign_file = _make_csv_files(tmp_path)
    _call(mount_file, sign_file, dry_run=True)

    run = StreetScanImportRun.objects.get(mount_file=mount_file, sign_file=sign_file)
    assert run.dry_run is True
