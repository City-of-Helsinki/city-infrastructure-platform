"""Tests for the clean_orphan_mounts_v2 management command."""
from io import StringIO

import pytest
from django.core.management import call_command

from traffic_control.analyze_utils.traffic_sign_data_v2_import import SOURCE_NAME
from traffic_control.models import MountReal
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountRealFactory,
    SignpostRealFactory,
    TrafficSignRealFactory,
)

CMD = "clean_orphan_mounts_v2"


def _call_command(**kwargs) -> tuple[str, str]:
    """Call the management command and capture stdout/stderr.

    Args:
        **kwargs: Keyword arguments forwarded to call_command.

    Returns:
        tuple[str, str]: (stdout output, stderr output).
    """
    stdout = StringIO()
    stderr = StringIO()
    call_command(CMD, stdout=stdout, stderr=stderr, **kwargs)
    return stdout.getvalue(), stderr.getvalue()


# ── No-orphan tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_no_orphans_reports_nothing_to_delete() -> None:
    """When no orphan mounts exist the command reports nothing to delete.

    Returns:
        None
    """
    stdout, _ = _call_command()

    assert "No orphan mounts found" in stdout


# ── Deletion tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_orphan_mount_is_hard_deleted() -> None:
    """An unreferenced MountReal with SOURCE_NAME is hard-deleted by the command.

    Returns:
        None
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)

    _call_command()

    assert not MountReal.objects.filter(id=mount.id).exists()


@pytest.mark.django_db
def test_delete_reports_count_and_source_name_in_stdout() -> None:
    """Stdout after deletion mentions the deleted count and the source name.

    Returns:
        None
    """
    MountRealFactory(source_name=SOURCE_NAME)
    MountRealFactory(source_name=SOURCE_NAME)

    stdout, _ = _call_command()

    assert "2" in stdout
    assert SOURCE_NAME in stdout


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sign_factory",
    [TrafficSignRealFactory, AdditionalSignRealFactory, SignpostRealFactory],
    ids=["traffic_sign", "additional_sign", "signpost"],
)
def test_only_orphan_mounts_are_deleted(sign_factory) -> None:
    """Only orphan mounts are deleted; referenced mounts survive the same run.

    Args:
        sign_factory: Factory class used to create the referencing sign record.

    Returns:
        None
    """
    orphan = MountRealFactory(source_name=SOURCE_NAME)
    referenced = MountRealFactory(source_name=SOURCE_NAME)
    sign_factory(source_name=SOURCE_NAME, mount_real=referenced)

    _call_command()

    assert not MountReal.objects.filter(id=orphan.id).exists()
    assert MountReal.objects.filter(id=referenced.id).exists()


# ── Preservation tests ─────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sign_factory",
    [TrafficSignRealFactory, AdditionalSignRealFactory, SignpostRealFactory],
    ids=["traffic_sign", "additional_sign", "signpost"],
)
def test_mount_referenced_by_sign_is_preserved(sign_factory) -> None:
    """Mount referenced by a sign with SOURCE_NAME is not deleted.

    Args:
        sign_factory: Factory class used to create the referencing sign record.

    Returns:
        None
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)
    sign_factory(source_name=SOURCE_NAME, mount_real=mount)

    _call_command()

    assert MountReal.objects.filter(id=mount.id).exists()


@pytest.mark.django_db
def test_mount_with_different_source_name_is_preserved() -> None:
    """A MountReal whose source_name differs from SOURCE_NAME is never touched.

    Returns:
        None
    """
    mount = MountRealFactory(source_name="other_source")

    _call_command()

    assert MountReal.objects.filter(id=mount.id).exists()


# ── Dry-run tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_dry_run_does_not_delete_orphan_mounts() -> None:
    """Dry-run mode makes no database changes.

    Returns:
        None
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)

    stdout, _ = _call_command(dry_run=True)

    assert MountReal.objects.filter(id=mount.id).exists()
    assert "DRY RUN" in stdout


@pytest.mark.django_db
def test_dry_run_default_detail_reports_count() -> None:
    """Dry-run without explicit --dry-run-detail defaults to showing the count.

    Returns:
        None
    """
    MountRealFactory(source_name=SOURCE_NAME)
    MountRealFactory(source_name=SOURCE_NAME)

    stdout, _ = _call_command(dry_run=True)

    assert "2" in stdout


@pytest.mark.django_db
def test_dry_run_count_detail_reports_count() -> None:
    """Dry-run with --dry-run-detail=count prints the number of orphan mounts.

    Returns:
        None
    """
    MountRealFactory(source_name=SOURCE_NAME)

    stdout, _ = _call_command(dry_run=True, dry_run_detail="count")

    assert "1" in stdout


@pytest.mark.django_db
def test_dry_run_ids_detail_prints_each_mount_id() -> None:
    """Dry-run with --dry-run-detail=ids prints each orphan mount UUID.

    Returns:
        None
    """
    mount = MountRealFactory(source_name=SOURCE_NAME)

    stdout, _ = _call_command(dry_run=True, dry_run_detail="ids")

    assert str(mount.id) in stdout
