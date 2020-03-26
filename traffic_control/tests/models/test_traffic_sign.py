from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import get_user


class TrafficSignRealTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.main_sign = TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )

    def test_main_sign_has_additional_signs_return_false(self):
        self.assertFalse(self.main_sign.has_additional_signs())

    def test_main_sign_has_additional_signs_return_true(self):
        TrafficSignReal.objects.create(
            parent=self.main_sign,
            location=Point(1, 1, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        self.assertTrue(self.main_sign.has_additional_signs())
