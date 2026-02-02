"""Tests for FormattedContentsAdminMixin."""
import pytest
from django.utils.translation import activate

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.mixins import FormattedContentsAdminMixin
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    TrafficControlDeviceTypeFactory,
)


class MockAdminWithMixin(FormattedContentsAdminMixin):
    """Mock admin class for testing the mixin."""

    pass


@pytest.fixture
def mock_admin() -> MockAdminWithMixin:
    """Create a mock admin instance.

    Returns:
        MockAdminWithMixin: Mock admin instance for testing.
    """
    return MockAdminWithMixin()


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__returns_dash_when_no_obj(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content returns '-' when obj is None.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    result = mock_admin.content(None)
    assert result == "-"


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__returns_dash_when_no_get_content_s_rows_method(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content returns '-' when obj doesn't have get_content_s_rows method.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """

    class ObjWithoutMethod:
        pass

    result = mock_admin.content(ObjWithoutMethod())
    assert result == "-"


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__returns_dash_when_content_s_rows_empty(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content returns '-' when content_s_rows is empty.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=None,
    )
    additional_sign = as_factory(device_type=device_type, content_s=None)

    result = mock_admin.content(additional_sign)
    assert result == "-"


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__returns_html_with_single_row(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content returns properly formatted HTML for a single content row.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {
                "limit": "Time limit",
            },
        },
    }
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    additional_sign = as_factory(device_type=device_type, content_s={"limit": 2})

    activate("en")
    result = mock_admin.content(additional_sign)

    assert result.startswith("<dl>")
    assert result.endswith("</dl>")
    assert "<dt>Time limit</dt>" in result
    assert "<dd>2</dd>" in result


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__returns_html_with_multiple_rows(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content returns properly formatted HTML for multiple content rows.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "propertyOrder": 0},
            "unit": {"type": "string", "propertyOrder": 1},
            "weekday_start": {"type": "integer", "propertyOrder": 2},
            "weekday_end": {"type": "integer", "propertyOrder": 3},
        },
        "propertiesTitles": {
            "en": {
                "limit": "Time limit",
                "unit": "Unit",
                "weekday_start": "Weekday start time",
                "weekday_end": "Weekday ending time",
            },
        },
    }
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    additional_sign = as_factory(
        device_type=device_type,
        content_s={
            "limit": 2,
            "unit": "h",
            "weekday_start": 8,
            "weekday_end": 18,
        },
    )

    activate("en")
    result = mock_admin.content(additional_sign)

    assert result.startswith("<dl>")
    assert result.endswith("</dl>")
    # Check that all content is present (unit is combined with limit)
    assert "<dt>Time limit</dt>" in result
    assert "<dd>2 h</dd>" in result
    assert "<dt>Weekday start time</dt>" in result
    assert "<dd>8</dd>" in result
    assert "<dt>Weekday ending time</dt>" in result
    assert "<dd>18</dd>" in result


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__escapes_html_in_values(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content properly escapes HTML in values to prevent XSS.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    schema = {
        "type": "object",
        "properties": {
            "custom_field": {"type": "string", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {
                "custom_field": "Custom Field",
            },
        },
    }
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    additional_sign = as_factory(
        device_type=device_type,
        content_s={"custom_field": "<script>alert('XSS')</script>"},
    )

    activate("en")
    result = mock_admin.content(additional_sign)

    # Ensure the script tag is escaped
    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    assert "<script>" not in result or result.count("<script>") == 0  # Should not have unescaped script tags


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__handles_none_values(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content handles None values correctly by displaying '-'.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """

    # Create a mock object with get_content_s_rows that returns None values
    class MockObj:
        def get_content_s_rows(self) -> list:
            """Return mock content with None value.

            Returns:
                list: List of tuples with content rows.
            """
            return [("Field", None)]

    result = mock_admin.content(MockObj())

    assert "<dt>Field</dt>" in result
    assert "<dd>-</dd>" in result


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__preserves_order(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content preserves the order of content_s_rows.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    schema = {
        "type": "object",
        "properties": {
            "field_a": {"type": "string", "propertyOrder": 0},
            "field_b": {"type": "string", "propertyOrder": 1},
            "field_c": {"type": "string", "propertyOrder": 2},
        },
        "propertiesTitles": {
            "en": {
                "field_a": "Field A",
                "field_b": "Field B",
                "field_c": "Field C",
            },
        },
    }
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    additional_sign = as_factory(
        device_type=device_type,
        content_s={"field_a": "A", "field_b": "B", "field_c": "C"},
    )

    activate("en")
    result = mock_admin.content(additional_sign)

    # Check that fields appear in the correct order
    index_a = result.index("Field A")
    index_b = result.index("Field B")
    index_c = result.index("Field C")

    assert index_a < index_b < index_c


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__content__handles_special_characters(mock_admin: MockAdminWithMixin, as_factory) -> None:
    """Test that content properly escapes special characters.

    Args:
        mock_admin (MockAdminWithMixin): Mock admin instance.
        as_factory: Factory for creating additional sign instances.
    """
    schema = {
        "type": "object",
        "properties": {
            "field": {"type": "string", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {
                "field": "Field & Title",
            },
        },
    }
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )
    additional_sign = as_factory(
        device_type=device_type,
        content_s={"field": "Value with & ampersand"},
    )

    activate("en")
    result = mock_admin.content(additional_sign)

    # Ensure special characters are escaped
    assert "&amp;" in result
    assert "<dt>Field &amp; Title</dt>" in result
    assert "<dd>Value with &amp; ampersand</dd>" in result
