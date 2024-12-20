import pytest
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry, MultiLineString, MultiPoint

from traffic_control.tests.factories import MountPlanFactory, MountRealFactory
from traffic_control.tests.test_base_api import (
    test_line,
    test_line_2,
    test_multi_polygon,
    test_point,
    test_point_2,
    test_polygon,
)
from traffic_control.tests.wfs.wfs_utils import (
    EPSG_3879_URN,
    geojson_crs,
    geojson_feature_id,
    geojson_feature_point_coordinates,
    geojson_get_features,
    gml_envelope,
    gml_feature_crs,
    gml_feature_geometry,
    gml_feature_id,
    gml_get_features,
    test_point_helsinki,
    wfs_get_features_geojson,
    wfs_get_features_gml,
)
from traffic_control.views.wfs.utils import YXGML32Renderer

TEST_MULTI_POINT = MultiPoint(test_point, test_point_2)
EXPECTED_MULTIPOINT = (
    '<ns0:MultiGeometry xmlns:ns0="http://www.opengis.net/gml/3.2" ns0:id="{object_id}"'
    ' srsName="urn:ogc:def:crs:EPSG::3879">'
    '<ns0:Point><ns0:pos srsDimension="3">6645449.071 25487927.144 0.0</ns0:pos></ns0:Point>'
    '<ns0:Point><ns0:pos srsDimension="3">6645445.071 25487923.144 0.0</ns0:pos></ns0:Point></ns0:MultiGeometry>'
)

TEST_MULTI_LINE = MultiLineString(test_line, test_line_2)
EXPECTED_MULTILINE = (
    '<ns0:MultiGeometry xmlns:ns0="http://www.opengis.net/gml/3.2" ns0:id="{object_id}"'
    ' srsName="urn:ogc:def:crs:EPSG::3879">'
    '<ns0:LineString><ns0:posList srsDimension="3">'
    "6645440.071 25487918.144 0.0 6645440.071 25487967.144 0.0"
    "</ns0:posList></ns0:LineString>"
    '<ns0:LineString><ns0:posList srsDimension="3">'
    "6645459.071 25487937.144 0.0 6645469.071 25487947.144 0.0</ns0:posList></ns0:LineString>"
    "</ns0:MultiGeometry>"
)

TEST_GEOMETRY_COLLECTION = GeometryCollection(test_point, test_multi_polygon)
EXPECTED_GEOMETRY_COLLECTION = (
    '<ns0:MultiGeometry xmlns:ns0="http://www.opengis.net/gml/3.2" ns0:id="{object_id}"'
    ' srsName="urn:ogc:def:crs:EPSG::3879">'
    '<ns0:Point><ns0:pos srsDimension="3">6645449.071 25487927.144 0.0</ns0:pos></ns0:Point>'
    "<ns0:MultiGeometry><ns0:Polygon><ns0:exterior>"
    '<ns0:LinearRing><ns0:posList srsDimension="3">'
    "6645440.071 25487918.144 0.0 6645489.071 25487918.144 0.0 6645489.071 25487967.144 0.0 "
    "6645440.071 25487967.144 0.0 6645440.071 25487918.144 0.0"
    "</ns0:posList></ns0:LinearRing></ns0:exterior></ns0:Polygon>"
    "<ns0:Polygon><ns0:exterior>"
    '<ns0:LinearRing><ns0:posList srsDimension="3">'
    "6646439.071 25488917.144 0.0 6646489.071 25488917.144 0.0 6646489.071 25488967.144 0.0 "
    "6646439.071 25488967.144 0.0 6646439.071 25488917.144 0.0"
    "</ns0:posList></ns0:LinearRing>"
    "</ns0:exterior></ns0:Polygon>"
    "</ns0:MultiGeometry></ns0:MultiGeometry>"
)


EXPECTED_POLYGON_LOCATION = (
    "6645440.071 25487918.144 0.0 "
    "6645489.071 25487918.144 0.0 "
    "6645489.071 25487967.144 0.0 "
    "6645440.071 25487967.144 0.0 "
    "6645440.071 25487918.144 0.0"
)

EXPECTED_MULTIPOLYGON = (
    '<ns0:MultiGeometry xmlns:ns0="http://www.opengis.net/gml/3.2" ns0:id="{object_id}"'
    ' srsName="urn:ogc:def:crs:EPSG::3879">'
    '<ns0:Polygon><ns0:exterior><ns0:LinearRing><ns0:posList srsDimension="3">'
    "6645440.071 25487918.144 0.0 6645489.071 25487918.144 0.0 "
    "6645489.071 25487967.144 0.0 6645440.071 25487967.144 0.0 "
    "6645440.071 25487918.144 0.0</ns0:posList>"
    "</ns0:LinearRing></ns0:exterior></ns0:Polygon>"
    '<ns0:Polygon><ns0:exterior><ns0:LinearRing><ns0:posList srsDimension="3">'
    "6646439.071 25488917.144 0.0 6646489.071 25488917.144 0.0 "
    "6646489.071 25488967.144 0.0 6646439.071 25488967.144 0.0 "
    "6646439.071 25488917.144 0.0</ns0:posList>"
    "</ns0:LinearRing></ns0:exterior></ns0:Polygon></ns0:MultiGeometry>"
)


def _get_expected_centroid_location(geometry):
    return f"{geometry.centroid.y} {geometry.centroid.x} 0.0"


@pytest.mark.parametrize(
    "model_name, factory, location, expected_location_value",
    (
        (
            "mountplan",
            MountPlanFactory,
            test_point_helsinki,
            f"{test_point_helsinki.y} {test_point_helsinki.x} {test_point_helsinki.z}",
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            test_point_helsinki,
            _get_expected_centroid_location(test_point_helsinki),
        ),
        (
            "mountreal",
            MountRealFactory,
            test_point_helsinki,
            f"{test_point_helsinki.y} {test_point_helsinki.x} {test_point_helsinki.z}",
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            test_point_helsinki,
            _get_expected_centroid_location(test_point_helsinki),
        ),
        (
            "mountplan",
            MountPlanFactory,
            test_polygon,
            EXPECTED_POLYGON_LOCATION,
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            test_polygon,
            _get_expected_centroid_location(test_polygon),
        ),
        (
            "mountreal",
            MountRealFactory,
            test_polygon,
            EXPECTED_POLYGON_LOCATION,
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            test_polygon,
            _get_expected_centroid_location(test_polygon),
        ),
        (
            "mountplan",
            MountPlanFactory,
            test_multi_polygon,
            EXPECTED_MULTIPOLYGON,
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            test_multi_polygon,
            _get_expected_centroid_location(test_multi_polygon),
        ),
        (
            "mountreal",
            MountRealFactory,
            test_multi_polygon,
            EXPECTED_MULTIPOLYGON,
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            test_multi_polygon,
            _get_expected_centroid_location(test_multi_polygon),
        ),
        ("mountplan", MountPlanFactory, test_line, " ".join(YXGML32Renderer.get_swapped_coordinates(test_line)[0])),
        (
            "mountplancentroid",
            MountPlanFactory,
            test_line,
            _get_expected_centroid_location(test_line),
        ),
        (
            "mountreal",
            MountRealFactory,
            test_line,
            " ".join(YXGML32Renderer.get_swapped_coordinates(test_line)[0]),
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            test_line,
            _get_expected_centroid_location(test_line),
        ),
        (
            "mountplan",
            MountPlanFactory,
            TEST_MULTI_POINT,
            EXPECTED_MULTIPOINT,
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            TEST_MULTI_POINT,
            _get_expected_centroid_location(TEST_MULTI_POINT),
        ),
        (
            "mountreal",
            MountRealFactory,
            TEST_MULTI_POINT,
            EXPECTED_MULTIPOINT,
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            TEST_MULTI_POINT,
            _get_expected_centroid_location(TEST_MULTI_POINT),
        ),
        (
            "mountplan",
            MountPlanFactory,
            TEST_MULTI_LINE,
            EXPECTED_MULTILINE,
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            TEST_MULTI_LINE,
            _get_expected_centroid_location(TEST_MULTI_LINE),
        ),
        (
            "mountreal",
            MountRealFactory,
            TEST_MULTI_LINE,
            EXPECTED_MULTILINE,
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            TEST_MULTI_LINE,
            _get_expected_centroid_location(TEST_MULTI_LINE),
        ),
        (
            "mountplan",
            MountPlanFactory,
            TEST_GEOMETRY_COLLECTION,
            EXPECTED_GEOMETRY_COLLECTION,
        ),
        (
            "mountplancentroid",
            MountPlanFactory,
            TEST_GEOMETRY_COLLECTION,
            _get_expected_centroid_location(TEST_GEOMETRY_COLLECTION),
        ),
        (
            "mountreal",
            MountRealFactory,
            TEST_GEOMETRY_COLLECTION,
            EXPECTED_GEOMETRY_COLLECTION,
        ),
        (
            "mountrealcentroid",
            MountRealFactory,
            TEST_GEOMETRY_COLLECTION,
            _get_expected_centroid_location(TEST_GEOMETRY_COLLECTION),
        ),
    ),
)
@pytest.mark.django_db
def test__wfs_mount__gml(model_name: str, factory, location: GEOSGeometry, expected_location_value):
    device = factory(location=location)
    geometry_type_str = (
        location.__class__.__name__ if model_name not in ("mountplancentroid", "mountrealcentroid") else "Point"
    )

    gml_xml = wfs_get_features_gml(model_name)
    features = gml_get_features(gml_xml, model_name)

    assert len(features) == 1
    feature = features[0]
    assert gml_feature_id(feature) == f"{model_name}.{device.id}"
    # Ensure the coordinate order is [Y,X,Z] EPSG:3879
    assert gml_feature_geometry(feature, geometry_type_str) == expected_location_value.format(
        object_id=f"{model_name}.{device.id}.1"
    )
    assert gml_feature_crs(feature, geometry_type_str) == EPSG_3879_URN
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


@pytest.mark.parametrize(
    "model_name, factory",
    (
        ("mountplan", MountPlanFactory),
        ("mountreal", MountRealFactory),
    ),
)
@pytest.mark.django_db
def test__wfs_mount__geojson(model_name: str, factory):
    device = factory(location=test_point_helsinki)

    geojson = wfs_get_features_geojson(model_name)

    features = geojson_get_features(geojson)
    assert len(features) == 1
    feature = features[0]

    assert geojson_crs(geojson) == EPSG_3879_URN

    assert geojson_feature_id(feature) == f"{model_name}.{device.id}"

    # Coordinate order is always [X,Y,Z] in GeoJSON
    assert geojson_feature_point_coordinates(feature) == [device.location.x, device.location.y, device.location.z]
