import pytest
from django.conf import settings
from django.contrib.gis.geos import LinearRing, LineString, MultiPolygon, Point, Polygon

from traffic_control.geometry_utils import get_3d_geometry

test_point2d = Point(1, 1, srid=settings.SRID)
test_linearring = LinearRing((0, 0), (0, 1), (1, 1), (1, 0), (0, 0), srid=settings.SRID)
test_polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=settings.SRID)
test_polygon_2 = Polygon(((1, 1), (1, 2), (2, 2), (2, 1), (1, 1)), srid=settings.SRID)
test_multi_polygon = MultiPolygon(test_polygon, test_polygon_2, srid=settings.SRID)
test_line_string = LineString((0, 0), (1, 1), srid=settings.SRID)


@pytest.mark.parametrize(
    "input_geom,expected_ewkt",
    (
        (test_point2d, "SRID=3879;POINT Z (1 1 5)"),
        (test_linearring, "SRID=3879;LINEARRING Z (0 0 5, 0 1 5, 1 1 5, 1 0 5, 0 0 5)"),
        (test_polygon, "SRID=3879;POLYGON Z ((0 0 5, 0 1 5, 1 1 5, 1 0 5, 0 0 5))"),
        (
            test_multi_polygon,
            "SRID=3879;MULTIPOLYGON Z (((0 0 5, 0 1 5, 1 1 5, 1 0 5, 0 0 5)), ((1 1 5, 1 2 5, 2 2 5, 2 1 5, 1 1 5)))",
        ),
        (test_line_string, "SRID=3879;LINESTRING Z (0 0 5, 1 1 5)"),
    ),
)
def test_convert_to_3d(input_geom, expected_ewkt):
    geom_3d = get_3d_geometry(input_geom, 5.0)
    assert get_3d_geometry(input_geom, 5.0).ewkt == expected_ewkt
    assert get_3d_geometry(geom_3d, 5.0).ewkt == expected_ewkt
