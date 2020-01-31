from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase

from traffic_control.models import Lifecycle, MountType, TrafficSignCode
from users.models import User


class TrafficControlAPIBaseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpw")
        self.client.login(username="testuser", password="testpw")
        self.test_lifecycle = Lifecycle.ACTIVE
        self.test_lifecycle_2 = Lifecycle.INACTIVE
        self.test_code = TrafficSignCode.objects.create(
            code="A11", description="Speed limit"
        )
        self.test_code_2 = TrafficSignCode.objects.create(
            code="A12", description="Weight limit"
        )
        self.test_type = MountType.PORTAL
        self.test_type_2 = MountType.WALL
        self.test_point = Point(
            25496366.48055263, 6675573.680776692, srid=settings.SRID
        )
