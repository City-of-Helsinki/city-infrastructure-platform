from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.admin import TrafficSignRealAdmin
from traffic_control.models import TrafficSignReal
from traffic_control.models.common import Lifecycle
from traffic_control.tests.factories import get_user


class MockRequest:
    pass


class TrafficSignRealAdminTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(10, 10, 5, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
            lifecycle=Lifecycle.ACTIVE,
        )
        self.site = AdminSite()

    def test_traffic_sign_real_admin_display_map_widget_for_location(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = get_user(admin=True)
        form = ma.get_form(request, self.traffic_sign_real)
        self.assertEqual(type(form.base_fields["location"].widget).__name__, "OLMap")

    def test_traffic_sign_admin_has_a_z_coord_field(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = get_user(admin=True)
        form = ma.get_form(request, self.traffic_sign_real)
        self.assertIn("z_coord", form.base_fields)

    def test_has_additional_signs_return_yes(self):
        TrafficSignReal.objects.create(
            parent=self.traffic_sign_real,
            location=Point(1, 1, 5, srid=settings.SRID),
            legacy_code="800",
            direction=0,
            order=1,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
        )
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        self.assertEqual(ma.has_additional_signs(self.traffic_sign_real), "Kyllä")

    def test_has_additional_signs_return_no(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        self.assertEqual(ma.has_additional_signs(self.traffic_sign_real), "Ei")
