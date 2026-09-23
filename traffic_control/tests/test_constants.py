"""Tests for traffic_control/constants.py."""
from decimal import Decimal

import pytest

from traffic_control.constants import (
    SignValueFamily,
    TRAFFIC_SIGN_VALUE_FAMILIES,
    validate_traffic_sign_value_families,
)


@pytest.mark.parametrize("family_code", TRAFFIC_SIGN_VALUE_FAMILIES.keys())
def test__traffic_sign_value_families__generic_code_not_in_subcodes(family_code: str):
    """Test that a family's generic_code does not appear as its own subcode."""
    family = TRAFFIC_SIGN_VALUE_FAMILIES[family_code]
    assert family.generic_code not in family.subcodes, (
        f"Family '{family_code}' has its generic_code '{family.generic_code}' " f"in its subcodes dict."
    )


@pytest.mark.parametrize("family_code", TRAFFIC_SIGN_VALUE_FAMILIES.keys())
def test__traffic_sign_value_families__default_not_in_subcode_values(family_code: str):
    """Test that a family's default_value is not equal to any of its subcode values."""
    family = TRAFFIC_SIGN_VALUE_FAMILIES[family_code]
    if family.default_value is not None:
        subcode_values = set(family.subcodes.values())
        assert family.default_value not in subcode_values, (
            f"Family '{family_code}' has default_value {family.default_value} "
            f"which matches one of its subcode values."
        )


def test__traffic_sign_value_families__no_duplicate_subcodes():
    """Test that no subcode appears in multiple families."""
    seen_subcodes = {}
    for family_code, family in TRAFFIC_SIGN_VALUE_FAMILIES.items():
        for subcode_code in family.subcodes:
            assert subcode_code not in seen_subcodes, (
                f"Subcode '{subcode_code}' appears in both family "
                f"'{seen_subcodes[subcode_code]}' and '{family_code}'."
            )
            seen_subcodes[subcode_code] = family_code


def test__validate_traffic_sign_value_families__passes_with_valid_data():
    """Test that validation passes when TRAFFIC_SIGN_VALUE_FAMILIES is valid."""
    # Should not raise
    validate_traffic_sign_value_families()


def test__validate_traffic_sign_value_families__catches_generic_code_in_subcodes():
    """Test that validation raises when a generic_code appears as its own subcode."""
    family = SignValueFamily(
        generic_code="TEST",
        default_value=Decimal("1.0"),
        subcodes={"TEST": Decimal("2.0")},
    )
    families = {"TEST": family}

    with pytest.raises(AssertionError, match="generic_code 'TEST' appears as its own subcode"):
        # Temporarily replace the global dict for this test
        import traffic_control.constants as const_module

        original = const_module.TRAFFIC_SIGN_VALUE_FAMILIES
        try:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = families
            validate_traffic_sign_value_families()
        finally:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = original


def test__validate_traffic_sign_value_families__catches_default_in_subcode_values():
    """Test that validation raises when a default_value matches a subcode value."""
    family = SignValueFamily(
        generic_code="TEST",
        default_value=Decimal("1.0"),
        subcodes={"TEST_1": Decimal("1.0"), "TEST_2": Decimal("2.0")},
    )
    families = {"TEST": family}

    with pytest.raises(AssertionError, match="default_value 1.0 matches subcode 'TEST_1'"):
        import traffic_control.constants as const_module

        original = const_module.TRAFFIC_SIGN_VALUE_FAMILIES
        try:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = families
            validate_traffic_sign_value_families()
        finally:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = original


def test__validate_traffic_sign_value_families__catches_duplicate_subcodes():
    """Test that validation raises when a subcode appears in multiple families."""
    families = {
        "TEST1": SignValueFamily(
            generic_code="TEST1",
            default_value=Decimal("1.0"),
            subcodes={"SHARED": Decimal("2.0")},
        ),
        "TEST2": SignValueFamily(
            generic_code="TEST2",
            default_value=Decimal("3.0"),
            subcodes={"SHARED": Decimal("4.0")},
        ),
    }

    with pytest.raises(AssertionError, match="Subcode 'SHARED' appears in both family"):
        import traffic_control.constants as const_module

        original = const_module.TRAFFIC_SIGN_VALUE_FAMILIES
        try:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = families
            validate_traffic_sign_value_families()
        finally:
            const_module.TRAFFIC_SIGN_VALUE_FAMILIES = original
