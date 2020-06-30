from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.admin import TrafficSignRealAdmin
from traffic_control.models import TrafficSignReal
from traffic_control.models.common import Lifecycle
from traffic_control.tests.factories import get_additional_sign_real, get_user


class MockRequest:
    pass


class TrafficSignRealAdminTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.admin = get_user(admin=True)
        self.traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(10, 10, 5, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner="test owner",
            lifecycle=Lifecycle.ACTIVE,
        )
        self.site = AdminSite()

    def test_traffic_sign_real_admin_display_map_widget_for_location(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        form = ma.get_form(request, self.traffic_sign_real)
        self.assertEqual(type(form.base_fields["location"].widget).__name__, "OLMap")

    def test_traffic_sign_admin_has_a_z_coord_field(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        form = ma.get_form(request, self.traffic_sign_real)
        self.assertIn("z_coord", form.base_fields)

    def test_has_additional_signs_return_yes(self):
        get_additional_sign_real(parent=self.traffic_sign_real)
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        self.assertEqual(ma.has_additional_signs(self.traffic_sign_real), "Kyllä")

    def test_has_additional_signs_return_no(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        self.assertEqual(ma.has_additional_signs(self.traffic_sign_real), "Ei")

    def test_save_model_set_created_by_and_updated_by_for_creating(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        traffic_sign_real = TrafficSignReal(
            location=Point(1, 1, 5, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            owner="test owner",
        )
        ma.save_model(request, traffic_sign_real, None, None)
        self.assertEqual(traffic_sign_real.created_by, self.admin)
        self.assertEqual(traffic_sign_real.updated_by, self.admin)

    def test_save_model_set_updated_by_for_updating(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        ma.save_model(request, self.traffic_sign_real, None, None)
        self.assertEqual(self.traffic_sign_real.created_by, self.user)
        self.assertEqual(self.traffic_sign_real.updated_by, self.admin)

    def test_delete_model_soft_delete_instance(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        ma.delete_model(request, self.traffic_sign_real)
        self.traffic_sign_real.refresh_from_db()
        self.assertFalse(self.traffic_sign_real.is_active)
        self.assertEqual(self.traffic_sign_real.deleted_by, self.admin)

    def test_get_queryset_exclude_soft_deleted(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        qs = ma.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        ma.delete_model(request, self.traffic_sign_real)
        qs = ma.get_queryset(request)
        self.assertEqual(qs.count(), 0)

    def test_delete_queryset_soft_delete_objects_in_queryset(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        ma.delete_model(request, self.traffic_sign_real)
        ma.delete_queryset(request, TrafficSignReal.objects.all())
        self.traffic_sign_real.refresh_from_db()
        self.assertFalse(self.traffic_sign_real.is_active)
