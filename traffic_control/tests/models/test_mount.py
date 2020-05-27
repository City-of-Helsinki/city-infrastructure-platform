from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.models import MountReal, TrafficSignReal
from traffic_control.tests.factories import get_mount_type, get_user


class MountRealTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.mount_type = get_mount_type(code="LIGHTPOLE", description="Lightpole")
        self.mount_real = MountReal.objects.create(
            location=Point(1, 1, srid=settings.SRID),
            type=self.mount_type,
            owner="test owner",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_ordered_traffic_signs_property_return_ordered_traffic_signs(self):
        traffic_sign_1 = TrafficSignReal.objects.create(
            location=Point(0, 0, 2, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        traffic_sign_2 = TrafficSignReal.objects.create(
            location=Point(0, 0, 2.5, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        traffic_sign_3 = TrafficSignReal.objects.create(
            location=Point(0, 0, 1.8, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            parent=traffic_sign_1,
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        self.assertQuerysetEqual(
            self.mount_real.ordered_traffic_signs,
            [repr(traffic_sign_2), repr(traffic_sign_1), repr(traffic_sign_3)],
        )
