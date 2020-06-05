from django.conf import settings
from django.contrib.gis.geos import Point
from django.test import TestCase

from traffic_control.forms import TrafficSignRealModelForm
from traffic_control.models import TrafficSignReal
from traffic_control.models.common import Lifecycle
from traffic_control.tests.factories import get_user


class TrafficSignRealModelFormTestCase(TestCase):
    def test_update_traffic_sign_real_3d_location(self):
        user = get_user()
        data = {
            "location": Point(5, 5, srid=settings.SRID),
            "z_coord": 20,
            "direction": 0,
            "created_by": user.id,
            "updated_by": user.id,
            "owner": "test owner",
            "lifecycle": Lifecycle.ACTIVE,
        }
        user = get_user()
        traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(10, 10, 5, srid=settings.SRID),
            direction=0,
            created_by=user,
            updated_by=user,
            owner="test owner",
            lifecycle=Lifecycle.ACTIVE,
        )
        form = TrafficSignRealModelForm(data=data, instance=traffic_sign_real)
        self.assertEqual(form.fields["z_coord"].initial, 5)
        self.assertTrue(form.is_valid())

        instance = form.save()
        self.assertEqual(instance.location, Point(5, 5, 20, srid=settings.SRID))

    def test_create_traffic_sign_real_3d_location(self):
        user = get_user()
        data = {
            "location": Point(10, 10, srid=settings.SRID),
            "z_coord": 20,
            "direction": 0,
            "created_by": user.id,
            "updated_by": user.id,
            "owner": "test owner",
            "lifecycle": Lifecycle.ACTIVE,
        }
        form = TrafficSignRealModelForm(data=data)
        form.is_valid()
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.location, Point(10, 10, 20, srid=settings.SRID))
