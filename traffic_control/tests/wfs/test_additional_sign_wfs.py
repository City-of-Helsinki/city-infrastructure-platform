import pytest

from traffic_control.tests.factories import get_additional_sign_plan, get_additional_sign_real
from traffic_control.tests.wfs.wfs_utils import (
    EPSG_3879_URN,
    geojson_crs,
    geojson_feature_id,
    geojson_feature_point_coordinates,
    geojson_get_features,
    gml_feature_crs,
    gml_feature_geometry,
    gml_feature_id,
    gml_get_features,
    test_point_helsinki,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)


@pytest.mark.parametrize(
    "model_name, factory",
    (
        ("additionalsignplan", get_additional_sign_plan),
        ("additionalsignreal", get_additional_sign_real),
    ),
)
@pytest.mark.django_db
def test__wfs_additional_sign__gml(model_name: str, factory):
    device = factory(location=test_point_helsinki)

    gml_xml = wfs_get_features_gml(model_name)

    features = gml_get_features(gml_xml, model_name)
    assert len(features) == 1
    feature = features[0]

    assert gml_feature_id(feature) == f"{model_name}.{device.id}"

    # Ensure the coordinate order is [Y,X,Z] EPSG:3879
    assert gml_feature_geometry(feature) == f"{device.location.y} {device.location.x} {device.location.z}"
    assert gml_feature_crs(feature) == EPSG_3879_URN


@pytest.mark.parametrize(
    "model_name, factory",
    (
        ("additionalsignplan", get_additional_sign_plan),
        ("additionalsignreal", get_additional_sign_real),
    ),
)
@pytest.mark.django_db
def test__wfs_additional_sign__geojson(model_name: str, factory):
    device = factory(location=test_point_helsinki)

    geojson = wfs_get_features_geojson(model_name)

    features = geojson_get_features(geojson)
    assert len(features) == 1
    feature = features[0]

    assert geojson_crs(geojson) == EPSG_3879_URN

    assert geojson_feature_id(feature) == f"{model_name}.{device.id}"

    # Coordinate order is always [X,Y,Z] in GeoJSON
    assert geojson_feature_point_coordinates(feature) == [device.location.x, device.location.y, device.location.z]
