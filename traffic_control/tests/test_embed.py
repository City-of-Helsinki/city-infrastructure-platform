import uuid

import pytest
from django.urls import reverse
from django.utils.translation import activate

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    MountPlanFactory,
    MountRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (TrafficSignPlanFactory, AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "traffic-sign-plan-embed"),
        (TrafficSignRealFactory, AdditionalSignRealFactory, MountRealFactory, "mount_real", "traffic-sign-real-embed"),
    ),
)
@pytest.mark.parametrize("has_additional_signs", (False, True))
@pytest.mark.parametrize("has_mount", (False, True))
@pytest.mark.django_db
def test__embed__traffic_sign__context(
    client,
    ts_factory,
    as_factory,
    mount_factory,
    mount_parameter,
    url_name,
    has_additional_signs,
    has_mount,
):
    """Test that the embedded view can be built and its context has the objects that it should."""

    if has_mount:
        mount = mount_factory()
    else:
        mount = None

    traffic_sign_type = TrafficControlDeviceTypeFactory(
        code="TS1",
        target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
    )

    traffic_sign = ts_factory(device_type=traffic_sign_type, **{mount_parameter: mount})

    if has_additional_signs:
        additional_sign_type_1 = TrafficControlDeviceTypeFactory(
            code="AS1",
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )
        additional_sign_type_2 = TrafficControlDeviceTypeFactory(
            code="AS2",
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )
        additional_sign_1 = as_factory(
            device_type=additional_sign_type_1,
            parent=traffic_sign,
            height=2,
            **{mount_parameter: mount},
        )
        additional_sign_2 = as_factory(
            device_type=additional_sign_type_2,
            parent=traffic_sign,
            height=1,
            **{mount_parameter: mount},
        )
    else:
        additional_sign_1 = None
        additional_sign_2 = None

    response = client.get(reverse(url_name, kwargs={"pk": traffic_sign.id}))
    assert response.status_code == 200
    # Must not deny frame-embedding embedded views
    assert response.headers.get("x-frame-options") != "DENY"

    context = response.context
    assert context.get("object") == traffic_sign
    assert context.get("traffic_sign_fields")[3][1] == traffic_sign.id

    assert context.get("traffic_sign_fields")[0][1] == traffic_sign_type.code

    if has_additional_signs:
        assert len(context.get("additional_signs")) == 2

        assert context.get("additional_signs")[0]["object"] == additional_sign_1
        assert context.get("additional_signs")[0]["fields"][3][1] == additional_sign_1.id

        assert context.get("additional_signs")[1]["object"] == additional_sign_2
        assert context.get("additional_signs")[1]["fields"][3][1] == additional_sign_2.id

        assert context.get("additional_signs")[0]["fields"][0][1] == additional_sign_type_1.code
        assert context.get("additional_signs")[1]["fields"][0][1] == additional_sign_type_2.code
    else:
        assert context.get("additional_signs") == []

    if has_mount:
        assert context.get("mount_fields")[0][1] == mount.mount_type.code
        assert context.get("mount_fields")[5][1] == mount.id
    else:
        assert context.get("mount_fields") == []


@pytest.mark.parametrize("url_name", ("traffic-sign-plan-embed", "traffic-sign-real-embed"))
@pytest.mark.django_db
def test__embed__traffic_sign__not_found(client, url_name):
    """Test that the embedded view returns 404 when the object is not found."""
    response = client.get(reverse(url_name, kwargs={"pk": uuid.uuid4()}))
    assert response.status_code == 404


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__empty_content(as_factory):
    """Test that get_content_s_rows returns empty list when content_s is None or empty."""
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "propertyOrder": 0},
            },
        },
    )

    # Test with None content_s
    additional_sign = as_factory(device_type=device_type, content_s=None)
    assert additional_sign.get_content_s_rows() == []

    # Test with empty content_s
    additional_sign.content_s = {}
    assert additional_sign.get_content_s_rows() == []


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__no_schema(as_factory):
    """Test that get_content_s_rows returns empty list when device type has no content_schema."""
    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=None,
    )

    additional_sign = as_factory(device_type=device_type, content_s={"limit": 2})
    assert additional_sign.get_content_s_rows() == []


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__ordered_by_property_order(as_factory):
    """Test that get_content_s_rows returns tuples ordered by propertyOrder field in schema."""
    schema = {
        "type": "object",
        "properties": {
            "unit": {"type": "string", "propertyOrder": 1},
            "limit": {"type": "integer", "propertyOrder": 0},
            "weekday_end": {"type": "integer", "propertyOrder": 3},
            "weekday_start": {"type": "integer", "propertyOrder": 2},
        },
        "propertiesTitles": {
            "en": {
                "unit": "Unit",
                "limit": "Time limit",
                "weekday_end": "Weekday ending time",
                "weekday_start": "Weekday start time",
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
            "weekday_end": 18,
            "limit": 2,
            "unit": "h",
            "weekday_start": 8,
        },
    )

    activate("en")
    rows = additional_sign.get_content_s_rows()

    # Should be ordered: limit (0), weekday_start (2), weekday_end (3)
    # unit is combined with limit, not shown separately
    assert len(rows) == 3
    assert rows[0] == ("Time limit", "2 h")
    assert rows[1] == ("Weekday start time", 8)
    assert rows[2] == ("Weekday ending time", 18)


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__localized_titles(as_factory):
    """Test that get_content_s_rows uses localized titles based on current language."""
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {
                "limit": "Time limit",
            },
            "fi": {
                "limit": "Aikarajoitus",
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
        content_s={"limit": 2},
    )

    # Test English
    activate("en")
    rows = additional_sign.get_content_s_rows()
    assert rows[0] == ("Time limit", 2)

    # Test Finnish
    activate("fi")
    rows = additional_sign.get_content_s_rows()
    assert rows[0] == ("Aikarajoitus", 2)


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__combines_unit_with_limit(as_factory):
    """Test that get_content_s_rows combines unit with limit field and excludes unit from output."""
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "propertyOrder": 0},
            "unit": {"type": "string", "propertyOrder": 1},
        },
        "propertiesTitles": {
            "en": {
                "limit": "Time limit",
                "unit": "Unit",
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
        content_s={"limit": 2, "unit": "h"},
    )

    activate("en")
    rows = additional_sign.get_content_s_rows()

    # Should only have one row with unit combined
    assert len(rows) == 1
    assert rows[0] == ("Time limit", "2 h")


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__combines_unit_with_distance(as_factory):
    """Test that get_content_s_rows combines unit with distance field and excludes unit from output."""
    schema = {
        "type": "object",
        "properties": {
            "distance": {"type": "integer", "propertyOrder": 0},
            "unit": {"type": "string", "propertyOrder": 1},
        },
        "propertiesTitles": {
            "en": {
                "distance": "Distance",
                "unit": "Unit",
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
        content_s={"distance": 100, "unit": "m"},
    )

    activate("en")
    rows = additional_sign.get_content_s_rows()

    # Should only have one row with unit combined
    assert len(rows) == 1
    assert rows[0] == ("Distance", "100 m")


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__fallback_to_property_name(as_factory):
    """Test that get_content_s_rows falls back to property name if no localized title exists."""
    schema = {
        "type": "object",
        "properties": {
            "custom_field": {"type": "string", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {},
        },
    }

    device_type = TrafficControlDeviceTypeFactory(
        code="AS1",
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        content_schema=schema,
    )

    additional_sign = as_factory(
        device_type=device_type,
        content_s={"custom_field": "test_value"},
    )

    activate("en")
    rows = additional_sign.get_content_s_rows()

    assert len(rows) == 1
    assert rows[0] == ("custom_field", "test_value")


@pytest.mark.parametrize("as_factory", (AdditionalSignPlanFactory, AdditionalSignRealFactory))
@pytest.mark.django_db
def test__get_content_s_rows__returns_tuples(as_factory):
    """Test that get_content_s_rows returns list of tuples, not dictionaries."""
    schema = {
        "type": "object",
        "properties": {
            "field1": {"type": "string", "propertyOrder": 0},
        },
        "propertiesTitles": {
            "en": {
                "field1": "Field 1",
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
        content_s={"field1": "value1"},
    )

    activate("en")
    rows = additional_sign.get_content_s_rows()

    assert isinstance(rows, list)
    assert len(rows) == 1
    assert isinstance(rows[0], tuple)
    assert len(rows[0]) == 2
    assert rows[0][0] == "Field 1"
    assert rows[0][1] == "value1"
