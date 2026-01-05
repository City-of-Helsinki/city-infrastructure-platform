from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.tests.factories import (
    get_mount_type,
    get_owner,
    get_user,
    MountRealFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


class MountRealTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.mount_type = get_mount_type(code="LIGHTPOLE", description="Lightpole")
        self.mount_real = MountRealFactory(
            location=Point(MIN_X + 2, MIN_Y + 1, 0, srid=settings.SRID),
            mount_type=self.mount_type,
            owner=get_owner(),
            created_by=self.user,
            updated_by=self.user,
        )

    def test_ordered_traffic_signs_property_return_ordered_traffic_signs(self):
        traffic_sign_1 = TrafficSignRealFactory(
            location=Point(MIN_X + 1, MIN_Y + 1, 2, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        traffic_sign_2 = TrafficSignRealFactory(
            location=Point(MIN_X + 1, MIN_Y + 1, 2.5, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        traffic_sign_3 = TrafficSignRealFactory(
            location=Point(MIN_X + 1, MIN_Y + 1, 1.8, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            mount_real=self.mount_real,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        self.assertQuerySetEqual(
            self.mount_real.ordered_traffic_signs,
            [traffic_sign_2, traffic_sign_1, traffic_sign_3],
        )
