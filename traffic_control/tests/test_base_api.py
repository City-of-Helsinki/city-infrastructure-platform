from django.conf import settings
from django.contrib.gis.geos import LineString, MultiPolygon, Point, Polygon

from traffic_control.tests.utils import MIN_X, MIN_Y

illegal_test_point = Point(0, 0, 0, srid=settings.SRID)
illegal_test_polygon = Polygon(
    (
        (0, 0, 0),
        (0, 1, 0),
        (1, 1, 0),
        (1, 0, 0),
        (0, 0, 0),
    ),
    srid=settings.SRID,
)
illegal_multipolygon = MultiPolygon(illegal_test_polygon, srid=settings.SRID)

test_point = Point(MIN_X + 10.0, MIN_Y + 10.0, 0.0, srid=settings.SRID)
test_point_2 = Point(MIN_X + 6.0, MIN_Y + 6, 0.0, srid=settings.SRID)
test_point_3 = Point(MIN_X + 100.0, MIN_Y + 100.0, 0.0, srid=settings.SRID)
test_point_4 = Point(MIN_X + 44.3, MIN_Y + 60.1, 0.0, srid=settings.SRID)
test_line = LineString((MIN_X + 1, MIN_Y + 1, 0.0), (MIN_X + 50.0, MIN_Y + 1, 0.0), srid=settings.SRID)
test_line_2 = LineString((MIN_X + 20.0, MIN_Y + 20.0, 0.0), (MIN_X + 30.0, MIN_Y + 30.0, 0.0), srid=settings.SRID)
test_line_3 = LineString((MIN_X + 40.0, MIN_Y + 40.0, 0.0), (MIN_X + 60.0, MIN_Y + 60.0, 0.0), srid=settings.SRID)
test_line_4 = LineString((MIN_X + 500.0, MIN_Y + 500.0, 0.0), (MIN_X + 500.0, MIN_Y + 550.0, 0.0), srid=settings.SRID)
test_polygon = Polygon(
    (
        (MIN_X + 1, MIN_Y + 1, 0.0),
        (MIN_X + 1, MIN_Y + 50.0, 0.0),
        (MIN_X + 50.0, MIN_Y + 50.0, 0.0),
        (MIN_X + 50.0, MIN_Y + 1, 0.0),
        (MIN_X + 1, MIN_Y + 1, 0.0),
    ),
    srid=settings.SRID,
)
test_polygon_2 = Polygon(
    (
        (MIN_X + 1000.0, MIN_Y + 1000.0, 0.0),
        (MIN_X + 1000.0, MIN_Y + 1050.0, 0.0),
        (MIN_X + 1050.0, MIN_Y + 1050.0, 0.0),
        (MIN_X + 1050.0, MIN_Y + 1000.0, 0.0),
        (MIN_X + 1000.0, MIN_Y + 1000.0, 0.0),
    ),
    srid=settings.SRID,
)
test_polygon_3 = Polygon(
    (
        (MIN_X + 100.0, MIN_Y + 100.0, 0.0),
        (MIN_X + 100.0, MIN_Y + 150.0, 0.0),
        (MIN_X + 150.0, MIN_Y + 150.0, 0.0),
        (MIN_X + 150.0, MIN_Y + 100.0, 0.0),
        (MIN_X + 100.0, MIN_Y + 100.0, 0.0),
    ),
    srid=settings.SRID,
)
test_multi_polygon = MultiPolygon(test_polygon, test_polygon_2, srid=settings.SRID)
test_multi_polygon_2 = MultiPolygon(test_polygon_2, test_polygon_3, srid=settings.SRID)

point_location_test_data = [
    (test_point, test_polygon, 1),
    (test_point_2, test_polygon, 1),
    (test_point_3, test_polygon, 0),
    (test_point_4, test_polygon, 0),
    (test_point, test_polygon_2, 0),
    (test_point_2, test_polygon_2, 0),
    (test_point_3, test_polygon_2, 0),
]

point_location_error_test_data = [
    (test_point, "invalid_test_string", "Invalid geometry value."),
    (test_point, 123123, "Invalid geometry value."),
]

line_location_test_data = [
    (test_line, test_polygon, 1),
    (test_line_2, test_polygon, 1),
    (test_line_3, test_polygon, 1),
    (test_line_4, test_polygon, 0),
    (test_line, test_polygon_2, 0),
    (test_line_2, test_polygon_2, 0),
    (test_line_3, test_polygon_2, 0),
    (test_line_4, test_polygon_2, 0),
]

line_location_error_test_data = [
    (test_line, "invalid_test_string", "Invalid geometry value."),
    (test_line, 123123, "Invalid geometry value."),
]


invalid_ewkt_str = """
SRID=3879;MULTIPOLYGON Z (((25496415.929282654 6673359.761058535 0, 25496415.6385598 6673350.891779969 0,
25496430.44581493 6673350.877332475 0, 25496430.171727654 6673359.043233639 0,
25496415.929282654 6673359.761058534 0)))
"""
