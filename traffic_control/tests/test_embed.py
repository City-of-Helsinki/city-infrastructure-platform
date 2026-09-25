import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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


@pytest.mark.parametrize(
    ("as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "additional-sign-plan-embed"),
        (AdditionalSignRealFactory, MountRealFactory, "mount_real", "additional-sign-real-embed"),
    ),
)
@pytest.mark.django_db
def test__embed__additional_sign__context(client, as_factory, mount_factory, mount_parameter, url_name):
    """Test that the additional sign embed view shows the sign's own fields."""
    mount = mount_factory()
    device_type = TrafficControlDeviceTypeFactory(code="AS1", target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)
    additional_sign = as_factory(device_type=device_type, **{mount_parameter: mount})

    response = client.get(reverse(url_name, kwargs={"pk": additional_sign.id}))
    assert response.status_code == 200
    # Must not deny frame-embedding embedded views
    assert response.headers.get("x-frame-options") != "DENY"

    context = response.context
    assert context.get("object") == additional_sign
    assert context.get("additional_sign_fields")[0][1] == device_type.code
    assert context.get("additional_sign_fields")[3][1] == additional_sign.id


@pytest.mark.parametrize("url_name", ("additional-sign-plan-embed", "additional-sign-real-embed"))
@pytest.mark.django_db
def test__embed__additional_sign__not_found(client, url_name):
    """Test that the additional sign embed view returns 404 when the object is not found."""
    response = client.get(reverse(url_name, kwargs={"pk": uuid.uuid4()}))
    assert response.status_code == 404


@pytest.mark.parametrize("url_name", ("mount-plan-embed", "mount-real-embed"))
@pytest.mark.django_db
def test__embed__mount__not_found(client, url_name):
    """Test that the mount embed view returns 404 when the object is not found."""
    response = client.get(reverse(url_name, kwargs={"pk": uuid.uuid4()}))
    assert response.status_code == 404


def _build_mount_with_devices(ts_factory, as_factory, mount_factory, mount_parameter):
    """Build a mount with two traffic signs, a child additional sign and a parentless one.

    Args:
        ts_factory: Traffic sign plan or real factory.
        as_factory: Additional sign plan or real factory.
        mount_factory: Mount plan or real factory.
        mount_parameter (str): Name of the mount field on the devices.

    Returns:
        tuple: The mount, both traffic signs, the child additional sign and the parentless one.
    """
    mount = mount_factory()
    ts_type = TrafficControlDeviceTypeFactory(code="TS1", target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)
    as_type = TrafficControlDeviceTypeFactory(code="AS1", target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)

    upper_sign = ts_factory(device_type=ts_type, **{mount_parameter: mount})
    lower_sign = ts_factory(device_type=ts_type, **{mount_parameter: mount})
    child_sign = as_factory(device_type=as_type, parent=upper_sign, height=2, **{mount_parameter: mount})
    parentless_sign = as_factory(device_type=as_type, parent=None, height=1, **{mount_parameter: mount})

    return mount, upper_sign, lower_sign, child_sign, parentless_sign


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (TrafficSignPlanFactory, AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "mount-plan-embed"),
        (TrafficSignRealFactory, AdditionalSignRealFactory, MountRealFactory, "mount_real", "mount-real-embed"),
    ),
)
@pytest.mark.django_db
def test__embed__mount__context(client, ts_factory, as_factory, mount_factory, mount_parameter, url_name):
    """Test that the mount embed view lists the mount's fields, traffic signs and additional signs."""
    mount, upper_sign, lower_sign, child_sign, parentless_sign = _build_mount_with_devices(
        ts_factory, as_factory, mount_factory, mount_parameter
    )

    response = client.get(reverse(url_name, kwargs={"pk": mount.id}))
    assert response.status_code == 200
    # Must not deny frame-embedding embedded views
    assert response.headers.get("x-frame-options") != "DENY"

    context = response.context
    assert context.get("object") == mount
    assert context.get("mount_fields")[0][1] == mount.mount_type.code
    assert context.get("mount_fields")[5][1] == mount.id

    traffic_signs = context.get("traffic_signs")
    assert {entry["object"] for entry in traffic_signs} == {upper_sign, lower_sign}

    by_object = {entry["object"]: entry for entry in traffic_signs}
    assert by_object[upper_sign]["fields"][3][1] == upper_sign.id
    assert [entry["object"] for entry in by_object[upper_sign]["additional_signs"]] == [child_sign]
    assert by_object[lower_sign]["additional_signs"] == []


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (TrafficSignPlanFactory, AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "mount-plan-embed"),
        (TrafficSignRealFactory, AdditionalSignRealFactory, MountRealFactory, "mount_real", "mount-real-embed"),
    ),
)
@pytest.mark.django_db
def test__embed__mount__lists_parentless_additional_signs(
    client, ts_factory, as_factory, mount_factory, mount_parameter, url_name
):
    """Test that the additional sign section is scoped by mount, so parentless signs are listed."""
    mount, _, _, child_sign, parentless_sign = _build_mount_with_devices(
        ts_factory, as_factory, mount_factory, mount_parameter
    )

    response = client.get(reverse(url_name, kwargs={"pk": mount.id}))

    additional_signs = response.context.get("additional_signs")
    # Ordered from top down by height
    assert [entry["object"] for entry in additional_signs] == [child_sign, parentless_sign]
    assert additional_signs[0]["fields"][3][1] == child_sign.id


def _build_mount_with_traffic_signs(ts_factory, as_factory, mount_factory, mount_parameter, count):
    """Build a mount carrying a given number of traffic signs, each with one additional sign.

    Args:
        ts_factory: Traffic sign plan or real factory.
        as_factory: Additional sign plan or real factory.
        mount_factory: Mount plan or real factory.
        mount_parameter (str): Name of the mount field on the devices.
        count (int): Number of traffic signs to attach to the mount.

    Returns:
        MountPlan | MountReal: The created mount.
    """
    mount = mount_factory()
    ts_type = TrafficControlDeviceTypeFactory(code="TS1", target_model=DeviceTypeTargetModel.TRAFFIC_SIGN)
    as_type = TrafficControlDeviceTypeFactory(code="AS1", target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN)

    for _unused in range(count):
        traffic_sign = ts_factory(device_type=ts_type, **{mount_parameter: mount})
        as_factory(device_type=as_type, parent=traffic_sign, height=1, **{mount_parameter: mount})

    return mount


@pytest.mark.parametrize(
    ("ts_factory", "as_factory", "mount_factory", "mount_parameter", "url_name"),
    (
        (TrafficSignPlanFactory, AdditionalSignPlanFactory, MountPlanFactory, "mount_plan", "mount-plan-embed"),
        (TrafficSignRealFactory, AdditionalSignRealFactory, MountRealFactory, "mount_real", "mount-real-embed"),
    ),
)
@pytest.mark.django_db
def test__embed__mount__query_count_does_not_grow_with_traffic_signs(
    client, ts_factory, as_factory, mount_factory, mount_parameter, url_name
):
    """Test that adding traffic signs to a mount does not add queries to the mount page."""
    small_mount = _build_mount_with_traffic_signs(ts_factory, as_factory, mount_factory, mount_parameter, 1)
    large_mount = _build_mount_with_traffic_signs(ts_factory, as_factory, mount_factory, mount_parameter, 5)

    # Warm up caches that are only populated on the first request of the process
    client.get(reverse(url_name, kwargs={"pk": small_mount.id}))

    with CaptureQueriesContext(connection) as small_queries:
        assert client.get(reverse(url_name, kwargs={"pk": small_mount.id})).status_code == 200

    with CaptureQueriesContext(connection) as large_queries:
        assert client.get(reverse(url_name, kwargs={"pk": large_mount.id})).status_code == 200

    assert len(large_queries) == len(small_queries)
