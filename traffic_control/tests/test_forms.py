from enum import member

from django.conf import settings
from django.contrib.gis.geos import Point
from django.forms import forms
from django.test import TestCase
from enumfields import Enum, EnumIntegerField

from traffic_control.enums import Lifecycle
from traffic_control.forms import AdminEnumChoiceField, TrafficSignRealModelForm
from traffic_control.models import TrafficSignReal
from traffic_control.tests.factories import get_owner, get_user, TrafficControlDeviceTypeFactory
from traffic_control.tests.utils import MIN_X, MIN_Y


class _TestEnum(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

    @member
    class Labels:
        RED = "Red"
        GREEN = "Green"
        # BLUE label is left out on purpose


class _TestForm(forms.Form):
    test_field = EnumIntegerField(_TestEnum).formfield(choices_form_class=AdminEnumChoiceField)


def test_admin_enum_choice_field():
    form = _TestForm()
    widget = form.fields["test_field"].widget
    context = widget.get_context("test_field", "", {})

    options = context["widget"]["optgroups"]

    assert options[0][1][0]["label"] == "---------"
    assert options[1][1][0]["label"] == "Red (1)"
    assert options[2][1][0]["label"] == "Green (2)"
    assert options[3][1][0]["label"] == "Blue (3)"


class TrafficSignRealModelFormTestCase(TestCase):
    def test_update_traffic_sign_real_3d_location_location_field(self):
        user = get_user()
        owner = get_owner()
        data = {
            "location": Point(MIN_X + 5, MIN_Y + 5, 0.0, srid=settings.SRID),
            "z_coord": 20,
            "direction": 0,
            "created_by": user.id,
            "updated_by": user.id,
            "owner": owner.pk,
            "lifecycle": Lifecycle.ACTIVE,
            "device_type": TrafficControlDeviceTypeFactory().pk,
        }
        user = get_user()
        traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(MIN_X + 10, MIN_Y + 10, 5, srid=settings.SRID),
            direction=0,
            created_by=user,
            updated_by=user,
            owner=owner,
            lifecycle=Lifecycle.ACTIVE,
        )
        form = TrafficSignRealModelForm(data=data, instance=traffic_sign_real)
        self.assertEqual(form.fields["z_coord"].initial, 5)
        self.assertTrue(form.is_valid())

    def test_update_traffic_sign_real_3d_location_location_ewkt_field(self):
        user = get_user()
        owner = get_owner()
        data = {
            "location": Point(MIN_X + 5, MIN_Y + 5, 0.0, srid=settings.SRID),
            "location_ewkt": Point(MIN_X + 8, MIN_Y + 8, 0.0, srid=settings.SRID).ewkt,
            "z_coord": 20,
            "direction": 0,
            "created_by": user.id,
            "updated_by": user.id,
            "owner": owner.pk,
            "lifecycle": Lifecycle.ACTIVE,
            "device_type": TrafficControlDeviceTypeFactory().pk,
        }
        user = get_user()
        traffic_sign_real = TrafficSignReal.objects.create(
            location=Point(MIN_X + 10, MIN_Y + 10, 5, srid=settings.SRID),
            direction=0,
            created_by=user,
            updated_by=user,
            owner=owner,
            lifecycle=Lifecycle.ACTIVE,
        )
        form = TrafficSignRealModelForm(data=data, instance=traffic_sign_real)
        self.assertEqual(form.fields["z_coord"].initial, 5)
        self.assertTrue(form.is_valid())

        instance = form.save()
        self.assertEqual(instance.location, Point(MIN_X + 8, MIN_Y + 8, 20, srid=settings.SRID))

    def test_create_traffic_sign_real_3d_location(self):
        user = get_user()
        data = {
            "location": Point(MIN_X + 10, MIN_Y + 10, 0.0, srid=settings.SRID),
            "z_coord": 20,
            "direction": 0,
            "created_by": user.id,
            "updated_by": user.id,
            "owner": get_owner().pk,
            "lifecycle": Lifecycle.ACTIVE,
            "device_type": TrafficControlDeviceTypeFactory().pk,
        }
        form = TrafficSignRealModelForm(data=data)
        form.is_valid()
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.location, Point(MIN_X + 10, MIN_Y + 10, 20, srid=settings.SRID))
