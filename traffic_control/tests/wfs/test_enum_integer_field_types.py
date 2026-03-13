"""Tests to verify that EnumIntegerField fields correctly declare xsd:string type in WFS schema.

This test module verifies the fix for the bug where EnumIntegerField fields were auto-detecting
as xsd:integer in the WFS GetCapabilities/DescribeFeatureType schema, while actually returning
string enum names in GetFeature responses.

The EnumIntegerNameXsdElement class forces these fields to declare xsd:string type to match
the actual returned values.
"""

from xml.etree import ElementTree

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from city_furniture.tests.factories import FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_api_client,
    MountPlanFactory,
    MountRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)

# XSD namespace for schema validation
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
APP_NAMESPACE = f"http://{settings.HOSTNAME}/wfs"

namespaces = {
    "xsd": XSD_NAMESPACE,
    "app": APP_NAMESPACE,
    "wfs": "http://www.opengis.net/wfs/2.0",
}


def wfs_url_describe_feature_type(type_names: str) -> str:
    """Build URL for WFS DescribeFeatureType request.

    Args:
        type_names: Comma-separated list of feature type names.

    Returns:
        str: Full URL for the DescribeFeatureType request.
    """
    return reverse(
        "wfs-city-infrastructure",
        query={
            "service": "WFS",
            "version": "2.0.0",
            "request": "DescribeFeatureType",
            "typeNames": type_names,
        },
    )


def get_describe_feature_type_schema(type_name: str) -> ElementTree.Element:
    """Get the XSD schema for a feature type from WFS DescribeFeatureType.

    Args:
        type_name: The feature type name to describe.

    Returns:
        ElementTree.Element: Root element of the XSD schema.
    """
    client = get_api_client()
    response = client.get(wfs_url_describe_feature_type(type_name))
    assert response.status_code == status.HTTP_200_OK

    # DescribeFeatureType returns regular HttpResponse, not streaming
    xml_content = response.content.decode("utf8")

    return ElementTree.fromstring(xml_content)


def get_element_type(schema: ElementTree.Element, feature_type_name: str, field_name: str) -> str | None:
    """Extract the XSD type declaration for a specific field in a feature type.

    Args:
        schema: The XSD schema root element.
        feature_type_name: Name of the feature type (e.g., 'mountreal').
        field_name: Name of the field to check (e.g., 'location_specifier').

    Returns:
        str | None: The XSD type (e.g., 'string', 'integer'), or None if not found.
    """
    # Find the top-level feature element first, then follow its declared type.
    feature_element = schema.find(f".//xsd:element[@name='{feature_type_name}']", namespaces)
    if feature_element is None:
        return None

    complex_type_name = feature_element.get("type")
    if not complex_type_name:
        return None

    # type can be namespaced, e.g. "app:MountRealType" -> keep only local part for @name lookup
    complex_type_local_name = complex_type_name.split(":")[-1]
    complex_type = schema.find(f".//xsd:complexType[@name='{complex_type_local_name}']", namespaces)
    if complex_type is None:
        return None

    # Field declarations are typically under complexContent/extension/sequence but this path is generic enough.
    element = complex_type.find(f".//xsd:element[@name='{field_name}']", namespaces)
    if element is None:
        return None

    element_type = element.get("type")
    if element_type is None:
        return None

    # DescribeFeatureType may return prefixed or non-prefixed XSD built-ins.
    return element_type.split(":")[-1]


# Test data: (feature_type_name, factory, field_name, expected_type)
ENUM_INTEGER_FIELD_TEST_CASES = [
    # Mount features - location_specifier, lifecycle
    ("mountreal", MountRealFactory, "location_specifier", "string"),
    ("mountreal", MountRealFactory, "lifecycle", "string"),
    ("mountplan", MountPlanFactory, "location_specifier", "string"),
    ("mountplan", MountPlanFactory, "lifecycle", "string"),
    ("mountrealcentroid", MountRealFactory, "location_specifier", "string"),
    ("mountrealcentroid", MountRealFactory, "lifecycle", "string"),
    ("mountplancentroid", MountPlanFactory, "location_specifier", "string"),
    ("mountplancentroid", MountPlanFactory, "lifecycle", "string"),
    # Traffic Sign features - location_specifier, condition, lifecycle
    ("trafficsignreal", TrafficSignRealFactory, "location_specifier", "string"),
    ("trafficsignreal", TrafficSignRealFactory, "condition", "string"),
    ("trafficsignreal", TrafficSignRealFactory, "lifecycle", "string"),
    ("trafficsignplan", TrafficSignPlanFactory, "location_specifier", "string"),
    ("trafficsignplan", TrafficSignPlanFactory, "lifecycle", "string"),
    # Additional Sign features - location_specifier, condition, color, lifecycle
    ("additionalsignreal", AdditionalSignRealFactory, "location_specifier", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "condition", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "color", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "lifecycle", "string"),
    ("additionalsignplan", AdditionalSignPlanFactory, "location_specifier", "string"),
    ("additionalsignplan", AdditionalSignPlanFactory, "color", "string"),
    ("additionalsignplan", AdditionalSignPlanFactory, "lifecycle", "string"),
    # Furniture Signpost features - arrow_direction, lifecycle
    ("furnituresignpostreal", FurnitureSignpostRealFactory, "arrow_direction", "string"),
    ("furnituresignpostreal", FurnitureSignpostRealFactory, "lifecycle", "string"),
    ("furnituresignpostplan", FurnitureSignpostPlanFactory, "arrow_direction", "string"),
    ("furnituresignpostplan", FurnitureSignpostPlanFactory, "lifecycle", "string"),
]


@pytest.mark.parametrize("feature_type,factory,field_name,expected_type", ENUM_INTEGER_FIELD_TEST_CASES)
@pytest.mark.django_db
def test_enum_integer_field_declares_string_type(feature_type: str, factory, field_name: str, expected_type: str):
    """Test that EnumIntegerField fields correctly declare string type in WFS schema.

    This verifies the fix for the bug where EnumIntegerField with EnumNameXsdElement
    would auto-detect as integer but return string enum names, causing type
    mismatches in WFS clients like QGIS.

    Args:
        feature_type: Name of the WFS feature type to test.
        factory: Factory class to create test data (ensures feature type exists).
        field_name: Name of the field to verify.
        expected_type: Expected XSD type declaration (should be "string").
    """
    # Create an instance to ensure the feature type has data
    factory()

    # Get the schema for this feature type
    schema = get_describe_feature_type_schema(feature_type)

    # Extract the type for the specified field
    actual_type = get_element_type(schema, feature_type, field_name)

    # Verify the type matches expected
    assert actual_type == expected_type, (
        f"Field '{field_name}' in feature type '{feature_type}' should declare type '{expected_type}' "
        f"but got '{actual_type}'. This field uses EnumIntegerField in the database but should "
        f"expose string enum names via EnumIntegerNameXsdElement."
    )


# Test data for EnumField fields that should remain as string (already working correctly)
ENUM_FIELD_TEST_CASES = [
    # These use EnumField (text-based) and EnumNameXsdElement - should already work
    ("trafficsignreal", TrafficSignRealFactory, "size", "string"),
    ("trafficsignreal", TrafficSignRealFactory, "reflection_class", "string"),
    ("trafficsignreal", TrafficSignRealFactory, "surface_class", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "size", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "reflection_class", "string"),
    ("additionalsignreal", AdditionalSignRealFactory, "surface_class", "string"),
]


@pytest.mark.parametrize("feature_type,factory,field_name,expected_type", ENUM_FIELD_TEST_CASES)
@pytest.mark.django_db
def test_enum_field_declares_string_type(feature_type: str, factory, field_name: str, expected_type: str):
    """Test that EnumField fields correctly declare xsd:string type in WFS schema.

    These fields use EnumField (text-based storage) with EnumNameXsdElement and should
    already work correctly. This test ensures we didn't break them with the fix.

    Args:
        feature_type: Name of the WFS feature type to test.
        factory: Factory class to create test data.
        field_name: Name of the field to verify.
        expected_type: Expected XSD type declaration (should be "string").
    """
    # Create an instance to ensure the feature type has data
    factory()

    # Get the schema for this feature type
    schema = get_describe_feature_type_schema(feature_type)

    # Extract the type for the specified field
    actual_type = get_element_type(schema, feature_type, field_name)

    # Verify the type matches expected
    assert actual_type == expected_type, (
        f"Field '{field_name}' in feature type '{feature_type}' should declare type '{expected_type}' "
        f"but got '{actual_type}'."
    )
