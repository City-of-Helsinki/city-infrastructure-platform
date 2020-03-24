from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase

from traffic_control.models import MountReal, TrafficSignReal
from traffic_control.tests.factories import get_user


class GenerateMountRealObjectsTestCase(TestCase):
    def setUp(self):
        self.user = get_user()

    def test_create_a_single_mount_real_for_main_and_additional_traffic_signs(self):
        main_sign = TrafficSignReal.objects.create(
            location=Point(0, 0, 10, srid=settings.SRID),
            legacy_code="100",
            mount_type="Lightpole",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        additional_sign = TrafficSignReal.objects.create(
            location=Point(0.5, 0.5, 5, srid=settings.SRID),
            parent=main_sign,
            legacy_code="800",
            mount_type="Lightpole",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        call_command("generate_mount_real_objects")
        main_sign.refresh_from_db()
        additional_sign.refresh_from_db()
        self.assertEqual(MountReal.objects.count(), 1)
        mount_real = MountReal.objects.first()
        self.assertEqual(main_sign.mount_real, mount_real)
        self.assertEqual(additional_sign.mount_real, mount_real)
