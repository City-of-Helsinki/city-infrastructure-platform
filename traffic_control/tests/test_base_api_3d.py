from django.conf import settings
from django.contrib.gis.geos import LineString, Point, Polygon

from traffic_control.tests.utils import MIN_X, MIN_Y

test_point_3d = Point(MIN_X + 6, MIN_Y + 6, 0.0, srid=settings.SRID)
test_point_2_3d = Point(MIN_X + 2, MIN_Y + 2, 0.0, srid=settings.SRID)
test_point_3_3d = Point(MIN_X + 100.0, MIN_Y + 100.0, 0.0, srid=settings.SRID)
test_point_4_3d = Point(MIN_X + 51, MIN_Y + 51, 0.0, srid=settings.SRID)
test_point_5_3d = Point(MIN_X + 150.0, MIN_Y + 1 + 150.0, 0.0, srid=settings.SRID)
test_line_3d = LineString((MIN_X + 1, MIN_Y + 1, 0.0), (MIN_X + 50.0, MIN_Y + 1, 0.0), srid=settings.SRID)
test_line_2_3d = LineString((MIN_X + 20.0, MIN_Y + 20.0, 0.0), (MIN_X + 30.0, MIN_Y + 30.0, 0.0), srid=settings.SRID)
test_line_3_3d = LineString((MIN_X + 40.0, MIN_Y + 40.0, 0.0), (MIN_X + 60.0, MIN_Y + 60.0, 0.0), srid=settings.SRID)
test_line_4_3d = LineString(
    (MIN_X + 500.0, MIN_Y + 500.0, 0.0), (MIN_X + 500.0, MIN_Y + 550.0, 0.0), srid=settings.SRID
)
test_polygon_3d = Polygon(
    (
        (MIN_X + 1, MIN_Y + 1, 0.0),
        (MIN_X + 1, MIN_Y + 50.0, 0.0),
        (MIN_X + 50.0, MIN_Y + 50.0, 0.0),
        (MIN_X + 50.0, MIN_Y + 1, 0.0),
        (MIN_X + 1, MIN_Y + 1, 0.0),
    ),
    srid=settings.SRID,
)
test_polygon_2_3d = Polygon(
    (
        (MIN_X + 1000.0, MIN_Y + 1000.0, 0.0),
        (MIN_X + 1000.0, MIN_Y + 1050.0, 0.0),
        (MIN_X + 1050.0, MIN_Y + 1050.0, 0.0),
        (MIN_X + 1050.0, MIN_Y + 1000.0, 0.0),
        (MIN_X + 1000.0, MIN_Y + 1000.0, 0.0),
    ),
    srid=settings.SRID,
)

point_location_test_data_3d = [
    (test_point_3d, test_polygon_3d, 1),
    (test_point_2_3d, test_polygon_3d, 1),
    (test_point_3_3d, test_polygon_3d, 0),
    (test_point_4_3d, test_polygon_3d, 0),
    (test_point_3d, test_polygon_2_3d, 0),
    (test_point_2_3d, test_polygon_2_3d, 0),
    (test_point_3_3d, test_polygon_2_3d, 0),
]

point_location_error_test_data_3d = [
    (test_point_3d, "invalid_test_string", "Invalid geometry value."),
    (test_point_3d, 123123, "Invalid geometry value."),
]

line_location_test_data_3d = [
    (test_line_3d, test_polygon_3d, 1),
    (test_line_2_3d, test_polygon_3d, 1),
    (test_line_3_3d, test_polygon_3d, 1),
    (test_line_4_3d, test_polygon_3d, 0),
    (test_line_3d, test_polygon_2_3d, 0),
    (test_line_2_3d, test_polygon_2_3d, 0),
    (test_line_3_3d, test_polygon_2_3d, 0),
    (test_line_4_3d, test_polygon_2_3d, 0),
]

line_location_error_test_data_3d = [
    (test_line_3d, "invalid_test_string", "Invalid geometry value."),
    (test_line_3d, 123123, "Invalid geometry value."),
]
