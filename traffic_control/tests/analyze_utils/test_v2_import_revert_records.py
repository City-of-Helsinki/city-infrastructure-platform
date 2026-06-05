"""Tests for revert record completeness in TrafficSignImporterV2.

Verifies that every _create_*_revert_record method captures all fields that are
overwritten during deactivation and update phases.
"""

import datetime
import json
import os

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_import import TrafficSignImporterV2
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountRealFactory,
    SignpostRealFactory,
    TrafficSignRealFactory,
    UserFactory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCANNED_AT = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
_SOURCE_NAME = "StreetScan2025-test"


def _make_stub_importer() -> TrafficSignImporterV2:
    """Create a minimal TrafficSignImporterV2 stub without calling __init__.

    Sets only the two attributes required by _write_revert_record so that
    the method can be exercised without loading any CSV files or building
    database lookup maps.

    Returns:
        TrafficSignImporterV2: Stub instance with dry_run=False and _revert_tmp=None.
    """
    importer: TrafficSignImporterV2 = object.__new__(TrafficSignImporterV2)
    importer.dry_run = False
    importer._revert_tmp = None
    return importer


def _read_revert_records(importer: TrafficSignImporterV2) -> list[dict]:
    """Flush and parse all JSONL records from the importer's revert temp file.

    Args:
        importer (TrafficSignImporterV2): Importer whose revert file to read.

    Returns:
        list[dict]: Parsed revert records in write order.
    """
    importer._revert_tmp.flush()
    with open(importer._revert_tmp.name, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _cleanup(importer: TrafficSignImporterV2) -> None:
    """Close and delete the importer's revert temp file if one was opened.

    Args:
        importer (TrafficSignImporterV2): Importer whose temp file to remove.
    """
    if importer._revert_tmp is not None:
        name = importer._revert_tmp.name
        importer._revert_tmp.close()
        os.unlink(name)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_importer() -> TrafficSignImporterV2:
    """Yield a stub importer and clean up its temp file after the test.

    Returns:
        TrafficSignImporterV2: Stub importer instance.
    """
    importer = _make_stub_importer()
    yield importer
    _cleanup(importer)


# ---------------------------------------------------------------------------
# Expected-dict builders for update (one per object type)
# ---------------------------------------------------------------------------


def _mount_update_expected(obj, user):
    return {
        "source_name": obj.source_name,
        "location": obj.location.ewkt if obj.location else None,
        "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
        "mount_type_id": str(obj.mount_type_id) if obj.mount_type_id else None,
        "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
        "attachment_url": obj.attachment_url,
        "updated_by_id": str(obj.updated_by_id) if obj.updated_by_id else None,
        "updated_at": str(obj.updated_at) if obj.updated_at else None,
    }


def _sign_update_expected(obj, user):
    return {
        "source_name": obj.source_name,
        "location": obj.location.ewkt if obj.location else None,
        "device_type_id": str(obj.device_type_id) if obj.device_type_id else None,
        "mount_real_id": str(obj.mount_real_id) if obj.mount_real_id else None,
        "mount_type_id": str(obj.mount_type_id) if obj.mount_type_id else None,
        "direction": obj.direction,
        "height": obj.height,
        "condition": str(obj.condition) if obj.condition else None,
        "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
        "value": str(obj.value) if obj.value is not None else None,
        "txt": obj.txt,
        "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
        "attachment_url": obj.attachment_url,
        "owner_id": str(obj.owner_id) if obj.owner_id else None,
        "installation_status": str(obj.installation_status) if obj.installation_status else None,
        "lifecycle": str(obj.lifecycle),
        "updated_by_id": str(obj.updated_by_id) if obj.updated_by_id else None,
        "updated_at": str(obj.updated_at) if obj.updated_at else None,
    }


def _signpost_update_expected(obj, user):
    return {
        "source_name": obj.source_name,
        "location": obj.location.ewkt if obj.location else None,
        "device_type_id": str(obj.device_type_id) if obj.device_type_id else None,
        "mount_real_id": str(obj.mount_real_id) if obj.mount_real_id else None,
        "direction": obj.direction,
        "height": str(obj.height) if obj.height is not None else None,
        "condition": obj.condition,
        "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
        "attachment_url": obj.attachment_url,
        "owner_id": str(obj.owner_id) if obj.owner_id else None,
        "mount_type_id": str(obj.mount_type_id) if obj.mount_type_id else None,
        "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
        "value": str(obj.value) if obj.value is not None else None,
        "txt": obj.txt,
        "updated_by_id": str(obj.updated_by_id) if obj.updated_by_id else None,
        "updated_at": str(obj.updated_at) if obj.updated_at else None,
    }


def _additional_sign_update_expected(obj, user):
    return {
        "source_name": obj.source_name,
        "location": obj.location.ewkt if obj.location else None,
        "device_type_id": str(obj.device_type_id) if obj.device_type_id else None,
        "parent_id": str(obj.parent_id) if obj.parent_id else None,
        "signpost_real_id": str(obj.signpost_real_id) if obj.signpost_real_id else None,
        "mount_real_id": str(obj.mount_real_id) if obj.mount_real_id else None,
        "direction": obj.direction,
        "height": str(obj.height) if obj.height is not None else None,
        "condition": obj.condition,
        "scanned_at": str(obj.scanned_at) if obj.scanned_at else None,
        "attachment_url": obj.attachment_url,
        "additional_information": obj.additional_information,
        "owner_id": str(obj.owner_id) if obj.owner_id else None,
        "mount_type_id": str(obj.mount_type_id) if obj.mount_type_id else None,
        "location_specifier": str(obj.location_specifier) if obj.location_specifier else None,
        "color": obj.color,
        "updated_by_id": str(obj.updated_by_id) if obj.updated_by_id else None,
        "updated_at": str(obj.updated_at) if obj.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Tests — deactivation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_cls,object_type_name",
    [
        (TrafficSignRealFactory, "TrafficSignReal"),
        (SignpostRealFactory, "SignpostReal"),
        (AdditionalSignRealFactory, "AdditionalSignReal"),
    ],
)
def test_deactivation_revert_old_contains_all_fields(
    stub_importer: TrafficSignImporterV2,
    factory_cls: type,
    object_type_name: str,
) -> None:
    """Deactivation revert record old dict must contain all fields with correct values.

    Args:
        stub_importer (TrafficSignImporterV2): Stub importer fixture.
        factory_cls (type): Factory class for the object type under test.
        object_type_name (str): Model class name string for the revert record.
    """
    user = UserFactory()
    obj = factory_cls(source_name=_SOURCE_NAME, scanned_at=_SCANNED_AT, updated_by=user)

    stub_importer._create_deactivation_revert_record(object_type_name, obj, obj.source_id)

    revert_records = _read_revert_records(stub_importer)
    assert len(revert_records) == 1
    assert revert_records[0]["old"] == {
        "lifecycle": str(obj.lifecycle),
        "validity_period_end": None,
        "scanned_at": str(_SCANNED_AT),
        "source_name": _SOURCE_NAME,
        "updated_by_id": str(user.pk),
        "updated_at": str(obj.updated_at),
    }


# ---------------------------------------------------------------------------
# Tests — update
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory_cls,revert_method,build_expected",
    [
        (MountRealFactory, "_write_mount_update_revert_record", _mount_update_expected),
        (TrafficSignRealFactory, "_create_sign_update_revert_record", _sign_update_expected),
        (SignpostRealFactory, "_create_signpost_update_revert_record", _signpost_update_expected),
        (AdditionalSignRealFactory, "_create_additional_sign_update_revert_record", _additional_sign_update_expected),
    ],
)
def test_update_revert_old_contains_all_fields(
    stub_importer: TrafficSignImporterV2,
    factory_cls: type,
    revert_method: str,
    build_expected,
) -> None:
    """Update revert record old dict must contain all updated fields with correct values.

    Args:
        stub_importer (TrafficSignImporterV2): Stub importer fixture.
        factory_cls (type): Factory class for the object type under test.
        revert_method (str): Name of the revert-record method to call on the importer.
        build_expected (Callable): Function taking (obj, user) returning the expected old dict.
    """
    user = UserFactory()
    obj = factory_cls(updated_by=user)

    getattr(stub_importer, revert_method)(obj, obj.source_id)

    revert_records = _read_revert_records(stub_importer)
    assert len(revert_records) == 1
    assert revert_records[0]["old"] == build_expected(obj, user)
