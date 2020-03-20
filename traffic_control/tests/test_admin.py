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
        self.traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(10, 10, 5, srid=settings.SRID),
            direction=0,
            order=1,
            created_by=get_user(),
            updated_by=get_user(),
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
