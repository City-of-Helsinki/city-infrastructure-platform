"""Tests for import_streetscan_signs_v2 management command parameter handling."""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data_v2_import import (
    VALID_OBJECT_TYPES,
    VALID_PHASES,
)

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
    """Create minimal mount and sign CSV files for testing.

    Args:
        tmp_path (Path): Pytest tmp_path fixture directory.

    Returns:
        tuple[str, str]: Paths to (mount_file, sign_file).
    """
    mount_file = _write_csv(tmp_path, _MOUNT_CSV_HEADER, [])
    sign_file = _write_csv(tmp_path, _SIGN_CSV_HEADER, [])
    return mount_file, sign_file


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


# ---------------------------------------------------------------------------
# _MOCK_SUMMARY used to short-circuit TrafficSignImporterV2.__init__ and .run()
# ---------------------------------------------------------------------------

_MOCK_SUMMARY: dict = {
    "object_types": list(VALID_OBJECT_TYPES),
    "phases": list(VALID_PHASES),
    "dry_run": False,
    "details": [],
}

_IMPORTER_PATH = "traffic_control.management.commands.import_streetscan_signs_v2.TrafficSignImporterV2"


# ===========================================================================
# Missing file validation
# ===========================================================================


def test_missing_mount_file_prints_error(tmp_path: Path) -> None:
    """Command prints an error to stderr when --mount-file does not exist.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    _, sign_file = _make_csv_files(tmp_path)
    stdout, stderr = _call("/nonexistent/mounts.csv", sign_file)
    assert "Mount file not found" in stderr
    assert stdout == ""


def test_missing_sign_file_prints_error(tmp_path: Path) -> None:
    """Command prints an error to stderr when --sign-file does not exist.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, _ = _make_csv_files(tmp_path)
    stdout, stderr = _call(mount_file, "/nonexistent/signs.csv")
    assert "Sign file not found" in stderr
    assert stdout == ""


def test_both_files_missing_reports_mount_error_first(tmp_path: Path) -> None:
    """When both files are missing the mount-file error is reported first.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    stdout, stderr = _call("/bad/mounts.csv", "/bad/signs.csv")
    assert "Mount file not found" in stderr


# ===========================================================================
# Defaults: omitting --object-type and --phase
# ===========================================================================


@pytest.mark.django_db
def test_default_object_types_and_phases(tmp_path: Path) -> None:
    """Omitting --object-type and --phase runs all four object types and all three phases.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        _, kwargs = mock_cls.call_args
        assert set(kwargs["object_types"]) == set(VALID_OBJECT_TYPES)
        assert set(kwargs["phases"]) == set(VALID_PHASES)


# ===========================================================================
# --object-type filtering
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize("object_type", list(VALID_OBJECT_TYPES))
def test_single_object_type_is_passed_to_importer(tmp_path: Path, object_type: str) -> None:
    """Specifying a single --object-type passes only that type to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        object_type (str): One of VALID_OBJECT_TYPES.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, object_types=[object_type])

        _, kwargs = mock_cls.call_args
        assert kwargs["object_types"] == [object_type]


@pytest.mark.django_db
def test_multiple_object_types_are_passed_to_importer(tmp_path: Path) -> None:
    """Specifying multiple --object-type values passes all of them to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, object_types=["signs", "additional-signs"])

        _, kwargs = mock_cls.call_args
        assert set(kwargs["object_types"]) == {"signs", "additional-signs"}


# ===========================================================================
# --phase filtering
# ===========================================================================


@pytest.mark.django_db
@pytest.mark.parametrize("phase", list(VALID_PHASES))
def test_single_phase_is_passed_to_importer(tmp_path: Path, phase: str) -> None:
    """Specifying a single --phase passes only that phase to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
        phase (str): One of VALID_PHASES.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, phases=[phase])

        _, kwargs = mock_cls.call_args
        assert kwargs["phases"] == [phase]


@pytest.mark.django_db
def test_multiple_phases_are_passed_to_importer(tmp_path: Path) -> None:
    """Specifying multiple --phase values passes all of them to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, phases=["create", "update"])

        _, kwargs = mock_cls.call_args
        assert set(kwargs["phases"]) == {"create", "update"}


# ===========================================================================
# --dry-run flag
# ===========================================================================


@pytest.mark.django_db
def test_dry_run_false_by_default(tmp_path: Path) -> None:
    """dry_run defaults to False when --dry-run is not provided.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        _, kwargs = mock_cls.call_args
        assert kwargs["dry_run"] is False


@pytest.mark.django_db
def test_dry_run_true_when_flag_set(tmp_path: Path) -> None:
    """dry_run is True when --dry-run is provided.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = {**_MOCK_SUMMARY, "dry_run": True}
        mock_cls.return_value = mock_instance

        stdout, _ = _call(mount_file, sign_file, dry_run=True)

        _, kwargs = mock_cls.call_args
        assert kwargs["dry_run"] is True
        assert "DRY RUN" in stdout


# ===========================================================================
# --resume flag
# ===========================================================================


@pytest.mark.django_db
def test_resume_false_by_default(tmp_path: Path) -> None:
    """resume defaults to False when --resume is not provided.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        _, kwargs = mock_cls.call_args
        assert kwargs["resume"] is False


@pytest.mark.django_db
def test_resume_true_when_flag_set(tmp_path: Path) -> None:
    """resume is True when --resume is provided.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, resume=True)

        _, kwargs = mock_cls.call_args
        assert kwargs["resume"] is True


# ===========================================================================
# --delimiter flag
# ===========================================================================


@pytest.mark.django_db
def test_default_delimiter_is_comma(tmp_path: Path) -> None:
    """Delimiter defaults to ',' when --delimiter is not provided.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        _, kwargs = mock_cls.call_args
        assert kwargs["delimiter"] == ","


@pytest.mark.django_db
def test_custom_delimiter_is_passed_to_importer(tmp_path: Path) -> None:
    """A custom --delimiter value is forwarded to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file, delimiter=";")

        _, kwargs = mock_cls.call_args
        assert kwargs["delimiter"] == ";"


# ===========================================================================
# File paths forwarded correctly
# ===========================================================================


@pytest.mark.django_db
def test_file_paths_are_passed_to_importer(tmp_path: Path) -> None:
    """mount_file and sign_file paths are forwarded verbatim to the importer.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        _, kwargs = mock_cls.call_args
        assert kwargs["mount_file"] == mount_file
        assert kwargs["sign_file"] == sign_file


# ===========================================================================
# Summary output
# ===========================================================================


@pytest.mark.django_db
def test_summary_section_appears_in_stdout(tmp_path: Path) -> None:
    """The import summary section header is always printed to stdout.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        stdout, _ = _call(mount_file, sign_file)

        assert "Import summary" in stdout


@pytest.mark.django_db
def test_error_details_printed_in_summary(tmp_path: Path) -> None:
    """Error entries in summary details are printed to stdout.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    error_summary = {
        **_MOCK_SUMMARY,
        "details": [{"level": "error", "source_id": "bad_id_1", "reason": "device type not found"}],
    }
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = error_summary
        mock_cls.return_value = mock_instance

        stdout, _ = _call(mount_file, sign_file)

        assert "bad_id_1" in stdout
        assert "device type not found" in stdout


@pytest.mark.django_db
def test_skip_and_warning_counts_in_summary(tmp_path: Path) -> None:
    """Skip and warning counts derived from details list are printed in the summary.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    detail_summary = {
        **_MOCK_SUMMARY,
        "details": [
            {"level": "skip", "source_id": "s1", "reason": "invalid geometry"},
            {"level": "skip", "source_id": "s2", "reason": "unreadable text"},
            {"level": "warning", "source_id": "w1", "reason": "missing mount"},
        ],
    }
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = detail_summary
        mock_cls.return_value = mock_instance

        stdout, _ = _call(mount_file, sign_file)

        assert "skipped" in stdout
        assert "warnings" in stdout


# ===========================================================================
# Importer is called exactly once
# ===========================================================================


@pytest.mark.django_db
def test_importer_run_called_once(tmp_path: Path) -> None:
    """The importer's run() method is called exactly once per command invocation.

    Args:
        tmp_path (Path): Pytest tmp_path fixture.
    """
    mount_file, sign_file = _make_csv_files(tmp_path)
    with patch(_IMPORTER_PATH) as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = _MOCK_SUMMARY
        mock_cls.return_value = mock_instance

        _call(mount_file, sign_file)

        mock_instance.run.assert_called_once()
