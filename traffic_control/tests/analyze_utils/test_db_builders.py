"""Tests for DbBuilderMixin._build_code_to_device_type_mapping."""

import pytest

from traffic_control.analyze_utils.traffic_sign_data_v2_db_builders import DbBuilderMixin
from traffic_control.tests.factories import TrafficControlDeviceTypeFactory


@pytest.mark.django_db
def test_build_code_to_device_type_mapping_maps_code_to_id() -> None:
    """Device type code is present in the mapping and resolves to the correct ID.

    Args: none

    Returns:
        None
    """
    dt = TrafficControlDeviceTypeFactory(code="A1", legacy_code="old-A1")

    result = DbBuilderMixin._build_code_to_device_type_mapping()

    assert result.get("A1") == dt.id


@pytest.mark.django_db
def test_build_code_to_device_type_mapping_excludes_legacy_code() -> None:
    """Legacy code must NOT appear as a key in the mapping.

    This guards against the previous bug where legacy_code was also inserted,
    causing ambiguous look-ups when a legacy value collided with a different
    device type's canonical code.

    Args: none

    Returns:
        None
    """
    TrafficControlDeviceTypeFactory(code="B2", legacy_code="old-B2")

    result = DbBuilderMixin._build_code_to_device_type_mapping()

    assert "old-B2" not in result


@pytest.mark.django_db
def test_build_code_to_device_type_mapping_multiple_device_types_all_codes_present() -> None:
    """All canonical codes appear as keys; no legacy code leaks into the mapping.

    Args: none

    Returns:
        None
    """
    dt1 = TrafficControlDeviceTypeFactory(code="C3", legacy_code="old-C3")
    dt2 = TrafficControlDeviceTypeFactory(code="D4", legacy_code="old-D4")

    result = DbBuilderMixin._build_code_to_device_type_mapping()

    assert result.get("C3") == dt1.id
    assert result.get("D4") == dt2.id
    assert "old-C3" not in result
    assert "old-D4" not in result


@pytest.mark.django_db
def test_build_code_to_device_type_mapping_same_code_and_legacy_code_value() -> None:
    """When code and legacy_code share the same string value the code is still mapped.

    Verifies that no duplicate key confusion arises even when the values happen
    to be identical (the legacy_code field is simply ignored).

    Args: none

    Returns:
        None
    """
    dt = TrafficControlDeviceTypeFactory(code="E5", legacy_code="E5")

    result = DbBuilderMixin._build_code_to_device_type_mapping()

    assert result.get("E5") == dt.id
    assert len([k for k in result if k == "E5"]) == 1
