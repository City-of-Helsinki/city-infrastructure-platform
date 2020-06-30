from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import get_additional_sign_real, get_user


class TrafficSignRealTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.main_sign = TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )

    def test_main_sign_has_additional_signs_return_false(self):
        self.assertFalse(self.main_sign.has_additional_signs())

    def test_main_sign_has_additional_signs_return_true(self):
        get_additional_sign_real(parent=self.main_sign)
        self.assertTrue(self.main_sign.has_additional_signs())

    def test_has_additional_signs_return_false_with_soft_deleted_additional_sign(self):
        additional_sign = get_additional_sign_real(parent=self.main_sign)
        additional_sign.soft_delete(self.user)
        self.assertFalse(self.main_sign.has_additional_signs())

    def test_soft_delete_main_traffic_sign_also_soft_delete_additional_sign(self):
        additional_sign = TrafficSignReal.objects.create(
            parent=self.main_sign,
            location=Point(1, 1, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        self.main_sign.soft_delete(self.user)
        additional_sign.refresh_from_db()
        self.assertFalse(additional_sign.is_active)
        self.assertEqual(additional_sign.deleted_by, self.user)
