from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase

from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import get_user


class LinkAdditionalTrafficSignsTestCase(TestCase):
    def setUp(self):
        self.user = get_user()

    def test_nearby_main_traffic_sign_is_linked(self):
        main_sign = TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(0.5, 0.5, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("link_additional_traffic_signs")
        additional_sign.refresh_from_db()
        self.assertEqual(additional_sign.parent, main_sign)

    def test_multiple_nearby_main_traffic_signs_immediate_above_one_linked(self):
        TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        main_sign_2 = TrafficSignReal.objects.create(
            location=Point(0, 0, 6, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(0.5, 0.5, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("link_additional_traffic_signs")
        additional_sign.refresh_from_db()
        self.assertEqual(additional_sign.parent, main_sign_2)

    def test_distant_main_traffic_sign_is_not_linked(self):
        TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(1, 1, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("link_additional_traffic_signs")
        additional_sign.refresh_from_db()
        self.assertIsNone(additional_sign.parent)

    def test_nearby_additional_traffic_sign_is_not_linked(self):
        TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="888",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(0.5, 0.5, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("link_additional_traffic_signs")
        additional_sign.refresh_from_db()
        self.assertIsNone(additional_sign.parent)

    def test_nearby_main_traffic_sign_below_additional_traffic_sign_is_not_linked(self):
        TrafficSignReal.objects.create(
            location=Point(0, 0, 3, srid=settings.SRID),
            legacy_code="888",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(0.5, 0.5, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("link_additional_traffic_signs")
        additional_sign.refresh_from_db()
        self.assertIsNone(additional_sign.parent)
