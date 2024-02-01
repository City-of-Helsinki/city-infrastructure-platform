from django.conf import settings
from django.contrib.gis.geos import LineString, Point, Polygon
from rest_framework.test import APITestCase

from traffic_control.enums import Lifecycle
from traffic_control.models import MountType, Owner, TrafficControlDeviceType
from users.models import User

test_point_3d = Point(10.0, 10.0, 0.0, srid=settings.SRID)
test_point_2_3d = Point(0.0, 0.0, 0.0, srid=settings.SRID)
test_point_3_3d = Point(100.0, 100.0, 0.0, srid=settings.SRID)
test_point_4_3d = Point(-44.3, 60.1, 0.0, srid=4326)
test_point_5_3d = Point(150.0, 150.0, 0.0, srid=settings.SRID)
test_line_3d = LineString((0.0, 0.0, 0.0), (50.0, 0.0, 0.0), srid=settings.SRID)
test_line_2_3d = LineString((20.0, 20.0, 0.0), (30.0, 30.0, 0.0), srid=settings.SRID)
test_line_3_3d = LineString((40.0, 40.0, 0.0), (60.0, 60.0, 0.0), srid=settings.SRID)
test_line_4_3d = LineString((500.0, 500.0, 0.0), (500.0, 550.0, 0.0), srid=settings.SRID)
test_polygon_3d = Polygon(
    (
        (0.0, 0.0, 0.0),
        (0.0, 50.0, 0.0),
        (50.0, 50.0, 0.0),
        (50.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    ),
    srid=settings.SRID,
)
test_polygon_2_3d = Polygon(
    (
        (1000.0, 1000.0, 0.0),
        (1000.0, 1050.0, 0.0),
        (1050.0, 1050.0, 0.0),
        (1050.0, 1000.0, 0.0),
        (1000.0, 1000.0, 0.0),
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
    (test_point_3d, "invalid_test_string", "Virheellinen geometria-arvo."),
    (test_point_3d, 123123, "Virheellinen geometria-arvo."),
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
    (test_line_3d, "invalid_test_string", "Virheellinen geometria-arvo."),
    (test_line_3d, 123123, "Virheellinen geometria-arvo."),
]


class TrafficControlAPIBaseTestCase3D(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="testuser", password="testpw", email="testuser@example.com")
        self.client.login(username="testuser", password="testpw")
        self.test_lifecycle = Lifecycle.ACTIVE
        self.test_lifecycle_2 = Lifecycle.INACTIVE
        self.test_device_type = TrafficControlDeviceType.objects.create(code="A11", description="Speed limit")
        self.test_device_type_2 = TrafficControlDeviceType.objects.create(code="A12", description="Weight limit")
        self.test_type = MountType.objects.create(code="PORTAL", description="Portal")
        self.test_type_2 = MountType.objects.create(code="WALL", description="Wall")
        self.test_point = test_point_3d
        self.test_point_2 = test_point_2_3d
        self.test_owner = Owner.objects.create(name_fi="Helsingin kaupunki", name_en="City of Helsinki")
