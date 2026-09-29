"""Tests for the ``distance_to_plan`` element of the WFS real device feature types."""

from typing import Callable, List, Optional
from xml.etree import ElementTree

import pytest
from django.contrib.gis.geos import Point

from city_furniture.tests.factories import FurnitureSignpostPlanFactory, FurnitureSignpostRealFactory
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_api_client,
    MountPlanFactory,
    MountRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.wfs.wfs_utils import (
    geojson_feature_id,
    geojson_feature_property,
    geojson_get_features,
    gml_feature_id,
    gml_feature_property,
    gml_get_features,
    test_point_helsinki,
    wfs_get_features_geojson,
    wfs_get_features_gml,
    wfs_url_get_features,
)

# WFS type name, real factory, plan factory, name of the plan foreign key on the real model
REAL_FEATURE_TYPES = [
    ("additionalsignreal", AdditionalSignRealFactory, AdditionalSignPlanFactory, "additional_sign_plan"),
    ("trafficsignreal", TrafficSignRealFactory, TrafficSignPlanFactory, "traffic_sign_plan"),
    ("signpostreal", SignpostRealFactory, SignpostPlanFactory, "signpost_plan"),
    ("mountreal", MountRealFactory, MountPlanFactory, "mount_plan"),
    ("mountrealcentroid", MountRealFactory, MountPlanFactory, "mount_plan"),
    ("furnituresignpostreal", FurnitureSignpostRealFactory, FurnitureSignpostPlanFactory, "furniture_signpost_plan"),
]


def _offset_point(east: float, north: float) -> Point:
    """Return a point offset from the shared Helsinki test point.

    Args:
        east (float): Offset along the x axis in meters.
        north (float): Offset along the y axis in meters.

    Returns:
        Point: The offset point, with the same Z value and SRID as the test point.
    """
    return Point(
        test_point_helsinki.x + east,
        test_point_helsinki.y + north,
        test_point_helsinki.z,
        srid=test_point_helsinki.srid,
    )


def _get_feature(features: List, model_name: str, real_id, id_getter: Callable):
    """Find the feature matching the given real device ID.

    Args:
        features (List): The features in the WFS response.
        model_name (str): The WFS type name, used to build the expected feature ID.
        real_id: ID of the real device whose feature is looked up.
        id_getter (Callable): Function returning the feature ID of a single feature.

    Returns:
        The matching feature.

    Raises:
        AssertionError: If no feature matches the given real device ID.
    """
    expected_id = f"{model_name}.{real_id}"
    matching = [feature for feature in features if id_getter(feature) == expected_id]
    assert len(matching) == 1, f"Expected exactly one feature with id {expected_id}, got {len(matching)}"
    return matching[0]


def _gml_distance(model_name: str, real_id) -> Optional[str]:
    """Read the ``distance_to_plan`` property of a single real feature from the GML response.

    Args:
        model_name (str): The WFS type name, e.g. ``"mountreal"``.
        real_id: ID of the real device whose feature is looked up.

    Returns:
        Optional[str]: The ``distance_to_plan`` property value as text.
    """
    features = gml_get_features(wfs_get_features_gml(model_name), model_name)
    return gml_feature_property(_get_feature(features, model_name, real_id, gml_feature_id), "distance_to_plan")


def _geojson_distance(model_name: str, real_id):
    """Read the ``distance_to_plan`` property of a single real feature from the GeoJSON response.

    Args:
        model_name (str): The WFS type name, e.g. ``"mountreal"``.
        real_id: ID of the real device whose feature is looked up.

    Returns:
        Any: The ``distance_to_plan`` property value.
    """
    features = geojson_get_features(wfs_get_features_geojson(model_name))
    return geojson_feature_property(_get_feature(features, model_name, real_id, geojson_feature_id), "distance_to_plan")


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__no_plan_is_null(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """A real that does not realize any plan has no distance."""
    real = real_factory(location=test_point_helsinki, **{plan_field: None})

    assert _gml_distance(model_name, real.id) is None
    assert _geojson_distance(model_name, real.id) is None


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__same_location_is_zero(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """A real installed exactly at its planned location has a distance of zero."""
    plan = plan_factory(location=test_point_helsinki)
    real = real_factory(location=test_point_helsinki, **{plan_field: plan})

    assert float(_gml_distance(model_name, real.id)) == 0.0
    assert _geojson_distance(model_name, real.id) == 0.0


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__offset_location(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """A 3-4-5 triangle offset in meters results in a distance of 5 meters."""
    plan = plan_factory(location=test_point_helsinki)
    real = real_factory(location=_offset_point(3, 4), **{plan_field: plan})

    assert float(_gml_distance(model_name, real.id)) == 5.0
    assert _geojson_distance(model_name, real.id) == 5.0


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__is_rounded_to_two_decimals(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """The distance is reported with centimeter precision."""
    plan = plan_factory(location=test_point_helsinki)
    real = real_factory(location=_offset_point(1.234567, 0), **{plan_field: plan})

    assert _geojson_distance(model_name, real.id) == 1.23


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__ignores_z_difference(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """The distance is measured in 2D, so a difference in height does not affect it."""
    plan = plan_factory(location=test_point_helsinki)
    elevated = Point(
        test_point_helsinki.x,
        test_point_helsinki.y,
        test_point_helsinki.z + 10,
        srid=test_point_helsinki.srid,
    )
    real = real_factory(location=elevated, **{plan_field: plan})

    assert _geojson_distance(model_name, real.id) == 0.0


@pytest.mark.parametrize("model_name, real_factory, plan_factory, plan_field", REAL_FEATURE_TYPES)
@pytest.mark.django_db
def test__wfs_real_distance_to_plan__is_published_as_double(
    model_name: str, real_factory, plan_factory, plan_field: str
) -> None:
    """DescribeFeatureType announces the element as a nillable double."""
    response = get_api_client().get(
        wfs_url_get_features(model_name).replace("request=GetFeature", "request=DescribeFeatureType")
    )
    schema = ElementTree.fromstring(response.content.decode("utf8"))

    elements = [
        element
        for element in schema.iter("{http://www.w3.org/2001/XMLSchema}element")
        if element.get("name") == "distance_to_plan"
    ]

    assert len(elements) == 1
    assert elements[0].get("type") == "double"
    assert elements[0].get("nillable") == "true"


@pytest.mark.django_db
def test__wfs_plan_feature_types_have_no_distance_to_plan() -> None:
    """The element is only published for real devices, not for the plans themselves."""
    response = get_api_client().get(
        wfs_url_get_features("trafficsignplan").replace("request=GetFeature", "request=DescribeFeatureType")
    )

    assert "distance_to_plan" not in response.content.decode("utf8")
