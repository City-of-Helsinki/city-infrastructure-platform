from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.test import TestCase

from traffic_control.models import MountReal, TrafficSignReal
from traffic_control.tests.factories import get_mount_type, get_owner, get_user


class GenerateMountRealObjectsTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.mount_type = get_mount_type(code="LIGHTPOLE", description="Lightpole")
        self.mount_type_2 = get_mount_type(code="POLE", description="Pole")

    def test_create_a_single_mount_real_for_nearby_traffic_signs(self):
        main_sign_1 = TrafficSignReal.objects.create(
            location=Point(1, 1, 10, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        main_sign_2 = TrafficSignReal.objects.create(
            location=Point(1, 0.8, 5, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        call_command("generate_mount_real_objects")
        self.assertEqual(MountReal.objects.count(), 1)
        mount_real = MountReal.objects.first()
        main_sign_1.refresh_from_db()
        main_sign_2.refresh_from_db()
        self.assertEqual(main_sign_1.mount_real, mount_real)
        self.assertEqual(main_sign_2.mount_real, mount_real)

    def test_create_separate_mount_reals_for_further_away_traffic_signs(self):
        TrafficSignReal.objects.create(
            location=Point(1, 1, 10, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        TrafficSignReal.objects.create(
            location=Point(2, 2, 5, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        call_command("generate_mount_real_objects")
        self.assertEqual(MountReal.objects.count(), 2)

    def test_create_separate_mount_reals_for_different_mount_type_traffic_signs(self):
        TrafficSignReal.objects.create(
            location=Point(1, 1, 10, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        TrafficSignReal.objects.create(
            location=Point(1, 0.8, 5, srid=settings.SRID),
            legacy_code="100",
            mount_type=self.mount_type_2,
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )
        call_command("generate_mount_real_objects")
        self.assertEqual(MountReal.objects.count(), 2)
