import pytest

from traffic_control.tests.factories import PlanFactory
from traffic_control.tests.wfs.wfs_utils import (
    EPSG_3879_URN,
    geojson_crs,
    geojson_feature_multipolygon_coordinates,
    geojson_get_features,
    gml_envelope,
    gml_feature_crs,
    gml_feature_geometry,
    gml_feature_id,
    gml_get_features,
    multipoly_inside_bbox,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)

EXPECTED_MULTIPOLYGON_XML = (
    '<ns0:MultiGeometry xmlns:ns0="http://www.opengis.net/gml/3.2" '
    'ns0:id="plan.{object_id}.1" '
    'srsName="urn:ogc:def:crs:EPSG::3879"><ns0:Polygon><ns0:exterior><ns0:LinearRing><ns0:posList '
    'srsDimension="3">6645450.071 25487920.144 0.0 6645451.071 25487920.144 0.0 '
    "6645451.071 25487921.144 0.0 6645450.071 25487921.144 0.0 6645450.071 "
    "25487920.144 "
    "0.0</ns0:posList></ns0:LinearRing></ns0:exterior></ns0:Polygon></ns0:MultiGeometry>"
)

EXPECTED_MULTIPOLYGON_COORDINATES = [
    [
        [
            [25487920.144, 6645450.071, 0.0],
            [25487920.144, 6645451.071, 0.0],
            [25487921.144, 6645451.071, 0.0],
            [25487921.144, 6645450.071, 0.0],
            [25487920.144, 6645450.071, 0.0],
        ]
    ]
]


@pytest.mark.django_db
def test__wfs_plan__gml():
    plan = PlanFactory(location=multipoly_inside_bbox)
    gml_xml = wfs_get_features_gml("plan")

    features = gml_get_features(gml_xml, "plan")
    assert len(features) == 1
    feature = features[0]

    assert gml_feature_id(feature) == f"plan.{plan.id}"

    # Ensure the coordinate order is [Y,X,Z] EPSG:3879
    assert gml_feature_geometry(feature, "MultiPolygon") == EXPECTED_MULTIPOLYGON_XML.format(object_id=plan.id)
    assert gml_feature_crs(feature, "MultiPolygon") == EPSG_3879_URN
    _assert_envelope(feature)


def _assert_envelope(feature):
    """assert that envelope coordinates are also swapped
    Testdata is done so that just coordinates bigger, small comparison is enough
    gte, lte comparisons because of Points and Linestrings
    """
    lower_corner, upper_corner = gml_envelope(feature)
    lower_y, lower_x = lower_corner.split(" ")
    upper_y, upper_x = upper_corner.split(" ")
    assert lower_y >= lower_x
    assert upper_y >= upper_x
    assert lower_x <= upper_x
    assert lower_y <= upper_y


@pytest.mark.django_db
def test__wfs_plan__geojson():
    PlanFactory(location=multipoly_inside_bbox)

    geojson = wfs_get_features_geojson("plan")

    features = geojson_get_features(geojson)
    assert len(features) == 1
    feature = features[0]

    assert geojson_crs(geojson) == EPSG_3879_URN

    # Coordinate order is always [X,Y,Z] in GeoJSON
    assert geojson_feature_multipolygon_coordinates(feature) == EXPECTED_MULTIPOLYGON_COORDINATES
