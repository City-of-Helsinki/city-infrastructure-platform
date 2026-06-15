"""Tests for TrafficSignImporterV2.get_orphan_mount_ids, clean_orphan_mounts and write_orphan_mounts_to_csv."""

import csv
from pathlib import Path

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME, TrafficSignImporterV2
from traffic_control.models import MountReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountRealFactory,
    SignpostRealFactory,
    TrafficSignRealFactory,
)

_OTHER_SOURCE = "other_source"


# ---------------------------------------------------------------------------
# get_orphan_mount_ids — parametrized: sign factory / source_name / expected
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sign_factory, sign_source_name, expected_orphan",
    (
        (None, None, True),
        (TrafficSignRealFactory, SOURCE_NAME, False),
        (AdditionalSignRealFactory, SOURCE_NAME, False),
        (SignpostRealFactory, SOURCE_NAME, False),
        (TrafficSignRealFactory, _OTHER_SOURCE, True),
    ),
)
def test_mount_orphan_status_by_referencing_sign(
    sign_factory: type | None,
    sign_source_name: str | None,
    expected_orphan: bool,
) -> None:
    """Mount orphan status depends on the referencing sign factory and its source_name.

    Covers: no referencing sign, each sign type with SOURCE_NAME (not orphan),
    and a TrafficSignReal with a different source_name (still orphan).

    The signpost_same_source case is a regression test for the old bug where
    AdditionalSignReal was checked twice instead of SignpostReal.

    Args:
        sign_factory (type | None): Factory class for the referencing sign, or None.
        sign_source_name (str | None): source_name to assign to the referencing sign.
        expected_orphan (bool): Whether the mount is expected to appear in the orphan set.
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)
    if sign_factory is not None:
        sign_factory(source_name=sign_source_name, mount_real=mount)

    result = TrafficSignImporterV2.get_orphan_mount_ids()

    if expected_orphan:
        assert mount.id in result
    else:
        assert mount.id not in result


# ---------------------------------------------------------------------------
# get_orphan_mount_ids — mount source_name scoping
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mount_with_other_source_name_not_included() -> None:
    """A mount whose source_name differs from SOURCE_NAME is never included in results.

    Mounts outside the SOURCE_NAME scope must not be treated as orphans.
    """
    other_mount = MountRealFactory(source_name=_OTHER_SOURCE)

    result = TrafficSignImporterV2.get_orphan_mount_ids()

    assert other_mount.id not in result


# ---------------------------------------------------------------------------
# get_orphan_mount_ids — mixed scenario
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mixed_mounts_only_true_orphans_returned() -> None:
    """Only mounts with no matching-source reference appear in the orphan set.

    Creates four mounts covering the distinct cases and verifies each lands in
    the correct bucket.
    """
    mount_orphan = MountRealFactory(source_name=SOURCE_NAME)
    mount_with_traffic_sign = MountRealFactory(source_name=SOURCE_NAME)
    mount_with_signpost = MountRealFactory(source_name=SOURCE_NAME)
    mount_other_source = MountRealFactory(source_name=_OTHER_SOURCE)

    TrafficSignRealFactory(source_name=SOURCE_NAME, mount_real=mount_with_traffic_sign)
    SignpostRealFactory(source_name=SOURCE_NAME, mount_real=mount_with_signpost)

    result = TrafficSignImporterV2.get_orphan_mount_ids()

    assert mount_orphan.id in result
    assert mount_with_traffic_sign.id not in result
    assert mount_with_signpost.id not in result
    assert mount_other_source.id not in result


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def orphan_mount() -> MountReal:
    """Create a MountReal with SOURCE_NAME not referenced by any sign or signpost.

    Returns:
        MountReal: An unreferenced mount scoped to SOURCE_NAME.
    """
    return MountRealFactory(source_name=SOURCE_NAME)


# ---------------------------------------------------------------------------
# clean_orphan_mounts
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_clean_orphan_mounts_hard_deletes_orphans(orphan_mount: MountReal) -> None:
    """Orphan mounts with SOURCE_NAME are permanently removed from the database.

    clean_orphan_mounts must perform a hard delete, not a soft delete,
    so the row is gone entirely after the call.

    Args:
        orphan_mount (MountReal): Unreferenced mount fixture.
    """
    TrafficSignImporterV2.clean_orphan_mounts()

    assert not MountReal.objects.filter(id=orphan_mount.id).exists()


@pytest.mark.django_db
def test_clean_orphan_mounts_preserves_referenced_mount() -> None:
    """A mount referenced by a TrafficSignReal with SOURCE_NAME is not deleted.

    Only true orphans must be removed; referenced mounts must survive the call.
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)
    TrafficSignRealFactory(source_name=SOURCE_NAME, mount_real=mount)

    TrafficSignImporterV2.clean_orphan_mounts()

    assert MountReal.objects.filter(id=mount.id).exists()


@pytest.mark.django_db
def test_clean_orphan_mounts_preserves_other_source_mount() -> None:
    """A mount whose source_name differs from SOURCE_NAME is not deleted.

    clean_orphan_mounts is scoped to SOURCE_NAME and must never touch mounts
    from other sources.
    """
    other_mount = MountRealFactory(source_name=_OTHER_SOURCE)

    TrafficSignImporterV2.clean_orphan_mounts()

    assert MountReal.objects.filter(id=other_mount.id).exists()


# ---------------------------------------------------------------------------
# write_orphan_mounts_to_csv
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_write_orphan_mounts_csv_headers(orphan_mount: MountReal, tmp_path: Path) -> None:
    """CSV produced by write_orphan_mounts_to_csv has the expected column headers.

    Args:
        orphan_mount (MountReal): Unreferenced mount fixture to ensure a row exists.
        tmp_path (Path): Pytest-provided temporary directory.
    """
    out_file = str(tmp_path / "orphans.csv")

    TrafficSignImporterV2.write_orphan_mounts_to_csv(out_file)

    with open(out_file, newline="") as fh:
        headers = next(csv.reader(fh))

    assert headers == ["location", "dbid", "mount_type", "source_id", "source_name"]


@pytest.mark.django_db
def test_write_orphan_mounts_csv_row_values(orphan_mount: MountReal, tmp_path: Path) -> None:
    """CSV rows contain correct field values for each orphan mount.

    Args:
        orphan_mount (MountReal): Unreferenced mount fixture.
        tmp_path (Path): Pytest-provided temporary directory.
    """
    out_file = str(tmp_path / "orphans.csv")

    TrafficSignImporterV2.write_orphan_mounts_to_csv(out_file)

    with open(out_file, newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 1
    row = rows[0]
    assert row["dbid"] == str(orphan_mount.id)
    assert row["source_id"] == orphan_mount.source_id
    assert row["source_name"] == orphan_mount.source_name
    assert row["mount_type"] == str(orphan_mount.mount_type)
    assert row["location"] == str(orphan_mount.location)


@pytest.mark.django_db
def test_write_orphan_mounts_csv_excludes_referenced_mount(tmp_path: Path) -> None:
    """Mounts with an active SOURCE_NAME reference are not written to the CSV.

    Args:
        tmp_path (Path): Pytest-provided temporary directory.
    """
    orphan = MountRealFactory(source_name=SOURCE_NAME)
    referenced = MountRealFactory(source_name=SOURCE_NAME)
    TrafficSignRealFactory(source_name=SOURCE_NAME, mount_real=referenced)

    out_file = str(tmp_path / "orphans.csv")
    TrafficSignImporterV2.write_orphan_mounts_to_csv(out_file)

    with open(out_file, newline="") as fh:
        written_ids = {row["dbid"] for row in csv.DictReader(fh)}

    assert str(orphan.id) in written_ids
    assert str(referenced.id) not in written_ids
