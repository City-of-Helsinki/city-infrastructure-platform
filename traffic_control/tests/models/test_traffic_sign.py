from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.models import AdditionalSignPlan, AdditionalSignReal, TrafficSignPlan, TrafficSignReal
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)
from traffic_control.tests.utils import MIN_X, MIN_Y


class TrafficSignPlanTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.main_sign = TrafficSignPlan.objects.create(
            location=Point(MIN_X + 1, MIN_Y + 1, 10, srid=settings.SRID),
            direction=0,
            device_type=get_traffic_control_device_type(code="T123"),
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
        )

    def test_main_sign_has_additional_signs_return_false(self):
        self.assertFalse(self.main_sign.has_additional_signs())

    def test_main_sign_has_additional_signs_return_true(self):
        get_additional_sign_plan(parent=self.main_sign)
        self.assertTrue(self.main_sign.has_additional_signs())

    def test_has_additional_signs_return_false_with_soft_deleted_additional_sign(self):
        additional_sign = get_additional_sign_plan(parent=self.main_sign)
        additional_sign.soft_delete(self.user)
        self.assertFalse(self.main_sign.has_additional_signs())

    def test_queryset_soft_delete_handles_additional_signs(self):
        get_additional_sign_plan(parent=get_traffic_sign_plan())
        additional_sign = get_additional_sign_plan(parent=self.main_sign)
        self.assertEqual(TrafficSignPlan.objects.count(), 2)
        TrafficSignPlan.objects.filter(pk=self.main_sign.pk).soft_delete(self.user)
        self.main_sign.refresh_from_db()
        additional_sign.refresh_from_db()
        self.assertFalse(self.main_sign.is_active)
        self.assertEqual(self.main_sign.deleted_by, self.user)
        self.assertFalse(additional_sign.is_active)
        self.assertEqual(additional_sign.deleted_by, self.user)
        self.assertEqual(TrafficSignPlan.objects.active().count(), 1)
        self.assertEqual(AdditionalSignPlan.objects.active().count(), 1)

    def test_soft_delete_without_additional_signs(self):
        self.main_sign.soft_delete(self.user)
        self.main_sign.refresh_from_db()
        self.assertFalse(self.main_sign.is_active)

    def test_soft_delete_main_traffic_sign_also_soft_delete_additional_sign(self):
        additional_sign = get_additional_sign_plan(parent=self.main_sign)
        self.main_sign.soft_delete(self.user)
        additional_sign.refresh_from_db()
        self.assertFalse(additional_sign.is_active)
        self.assertEqual(additional_sign.deleted_by, self.user)


class TrafficSignRealTestCase(TestCase):
    def setUp(self):
        self.user = get_user()
        self.main_sign = TrafficSignReal.objects.create(
            location=Point(MIN_X + 1, MIN_Y + 1, 10, srid=settings.SRID),
            legacy_code="100",
            direction=0,
            created_by=self.user,
            updated_by=self.user,
            owner=get_owner(),
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

    def test_queryset_soft_delete_handles_additional_signs(self):
        get_additional_sign_real(parent=get_traffic_sign_real())
        additional_sign = get_additional_sign_real(parent=self.main_sign)
        self.assertEqual(TrafficSignReal.objects.count(), 2)
        TrafficSignReal.objects.filter(pk=self.main_sign.pk).soft_delete(self.user)
        self.main_sign.refresh_from_db()
        additional_sign.refresh_from_db()
        self.assertFalse(self.main_sign.is_active)
        self.assertEqual(self.main_sign.deleted_by, self.user)
        self.assertFalse(additional_sign.is_active)
        self.assertEqual(additional_sign.deleted_by, self.user)
        self.assertEqual(TrafficSignReal.objects.active().count(), 1)
        self.assertEqual(AdditionalSignReal.objects.active().count(), 1)

    def test_soft_delete_without_additional_signs(self):
        self.main_sign.soft_delete(self.user)
        self.main_sign.refresh_from_db()
        self.assertFalse(self.main_sign.is_active)

    def test_soft_delete_main_traffic_sign_also_soft_delete_additional_sign(self):
        additional_sign = get_additional_sign_real(parent=self.main_sign)
        self.main_sign.soft_delete(self.user)
        additional_sign.refresh_from_db()
        self.assertFalse(additional_sign.is_active)
        self.assertEqual(additional_sign.deleted_by, self.user)
