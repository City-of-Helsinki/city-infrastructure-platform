from datetime import datetime

from auditlog.models import LogEntry
from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.gis.geos import Point
from django.test import RequestFactory, TestCase

from traffic_control.admin import BarrierRealAdmin, TrafficSignRealAdmin
from traffic_control.enums import Lifecycle
from traffic_control.models import BarrierReal, TrafficSignReal
from traffic_control.tests.factories import get_additional_sign_real, get_barrier_real, get_owner, get_user
from traffic_control.tests.utils import MIN_X, MIN_Y


class MockRequest:
    pass


class TrafficSignRealAdminTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.admin = get_user(admin=True)
        self.traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(MIN_X + 10, MIN_Y + 5, 5, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
            lifecycle=Lifecycle.ACTIVE,
        )
        self.site = AdminSite()

    def test_traffic_sign_real_admin_display_map_widget_for_location(self):
        ma = TrafficSignRealAdmin(TrafficSignReal, self.site)
        request = MockRequest()
        request.user = self.admin
        form = ma.get_form(request, self.traffic_sign_real)
        self.assertEqual(type(form.base_fields["location"].widget).__name__, "CityInfra3DOSMWidget")

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
            location=Point(MIN_X + 1, MIN_Y + 1, 5, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            owner=get_owner(),
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


class SoftDeleteAdminTestCase(TestCase):
    request_factory = RequestFactory()

    def setUp(self):
        self.admin_user = get_user(admin=True)
        self.barrier_real = get_barrier_real()
        self.site = AdminSite()
        self.model_admin = BarrierRealAdmin(BarrierReal, self.site)

    def test_exclude_soft_deleted_by_default(self):
        request = self.request_factory.get("/", {})
        request.user = self.admin_user
        changelist = self.model_admin.get_changelist_instance(request)
        qs = changelist.get_queryset(request)
        self.assertEqual(qs.count(), 1)
        self.model_admin.delete_model(request, self.barrier_real)
        qs = self.model_admin.get_queryset(request)
        self.assertEqual(qs.count(), 0)

    def test_list_soft_deleted(self):
        request = self.request_factory.get("/", {"soft_deleted": "1"})
        request.user = self.admin_user
        changelist = self.model_admin.get_changelist_instance(request)
        qs = changelist.get_queryset(request)
        self.assertEqual(qs.count(), 0)
        self.barrier_real.soft_delete(self.admin_user)
        qs = changelist.get_queryset(request)
        self.assertEqual(qs.count(), 1)

    def test_action_soft_delete(self):
        request = self.request_factory.post("/")
        request.user = self.admin_user
        self.model_admin.action_soft_delete(request, BarrierReal.objects.all())
        self.barrier_real.refresh_from_db()
        self.assertFalse(self.barrier_real.is_active)
        self.assertIsInstance(self.barrier_real.deleted_at, datetime)
        self.assertEqual(self.barrier_real.deleted_by, self.admin_user)

        # LogEntries appear to be done by system user as no login is actually performed
        # -> actor == None. A separate ticket for writing better test cases for soft deletes is created
        create_entries = LogEntry.objects.get_for_object(self.barrier_real).filter(action=LogEntry.Action.CREATE)
        self.assertEqual(create_entries.count(), 1)
        create_entry = create_entries[0]
        self.assertEqual(create_entry.actor, None)
        update_entries = LogEntry.objects.get_for_object(self.barrier_real).filter(action=LogEntry.Action.UPDATE)
        self.assertEqual(update_entries.count(), 1)
        update_entry = create_entries[0]
        self.assertEqual(update_entry.actor, None)
