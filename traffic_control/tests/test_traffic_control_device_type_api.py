import json

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import TrafficControlDeviceType
from traffic_control.tests.factories import (
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_control_device_type,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)
from users.models import User


class TrafficControlDeviceTypeTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="testadmin", password="testpw", email="testadmin@anders.fi"
        )
        self.user = User.objects.create_user(username="testuser", password="testpw")

    def test__list__as_user__ok(self):
        """
        Ensure that user can get list of traffic control device type objects.
        """
        self.client.force_login(self.user)
        count = 3
        for i in range(count):
            TrafficControlDeviceType.objects.create(
                code=i,
                description="Test description %s" % i,
            )
        response = self.client.get(reverse("v1:trafficcontroldevicetype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__list__as_admin__ok(self):
        """
        Ensure that admin can get list of traffic control device type objects.
        """
        self.client.force_login(self.admin_user)
        count = 3
        for i in range(count):
            TrafficControlDeviceType.objects.create(
                code=i,
                description="Test description %s" % i,
            )
        response = self.client.get(reverse("v1:trafficcontroldevicetype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test__retrieve__as_user__ok(self):
        """
        Ensure that user can get one traffic control device type object.
        """
        self.client.force_login(self.user)
        device_type = self.__create_test_traffic_control_device_type()
        response = self.client.get(reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(device_type.id))

    def test__retrieve__as_admin__ok(self):
        """
        Ensure that admin can get one traffic control device type object.
        """
        self.client.force_login(self.admin_user)
        device_type = self.__create_test_traffic_control_device_type()
        response = self.client.get(reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(device_type.id))

    def test__create__as_user__forbidden(self):
        """
        Ensure that user cannot create a new traffic control device type object.
        """
        self.client.force_login(self.user)
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.post(reverse("v1:trafficcontroldevicetype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 0)

    def test__create__as_admin__created(self):
        """
        Ensure admin can create a new traffic control device type object.
        """
        self.client.force_login(self.admin_user)
        data = {
            "code": "L3",
            "description": "Suojatie",
            "target_model": DeviceTypeTargetModel.ADDITIONAL_SIGN.value,
        }
        response = self.client.post(reverse("v1:trafficcontroldevicetype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 1)
        device_type = TrafficControlDeviceType.objects.first()
        self.assertEqual(device_type.code, data["code"])
        self.assertEqual(device_type.description, data["description"])

    def test__create_existing__bad_request(self):
        """
        Ensure that API will not create a new traffic control device type object with duplicated code-value.
        """
        self.client.force_login(self.admin_user)
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.post(reverse("v1:trafficcontroldevicetype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse("v1:trafficcontroldevicetype-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 1)
        device_type = TrafficControlDeviceType.objects.first()
        self.assertEqual(device_type.code, data["code"])
        self.assertEqual(device_type.description, data["description"])

    def test__update__as_user__forbidden(self):
        """
        Ensure that user cannot update existing traffic control device type object.
        """
        self.client.force_login(self.user)
        device_type = self.__create_test_traffic_control_device_type()
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.put(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 1)

    def test__update__as_admin__ok(self):
        """
        Ensure that admin can update existing traffic control device type object.
        """
        self.client.force_login(self.admin_user)
        device_type = self.__create_test_traffic_control_device_type()
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.put(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 1)
        device_type = TrafficControlDeviceType.objects.first()
        self.assertEqual(device_type.code, data["code"])
        self.assertEqual(device_type.description, data["description"])

    def test__destroy__as_user__forbidden(self):
        """
        Ensure user cannot delete traffic control device type object.
        """
        self.client.force_login(self.user)
        device_type = self.__create_test_traffic_control_device_type()
        response = self.client.delete(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 1)

    def test__destroy__as_admin__success(self):
        """
        Ensure that admin can delete traffic control device type object.
        """
        self.client.force_login(self.admin_user)
        device_type = self.__create_test_traffic_control_device_type()
        response = self.client.delete(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 0)

    def test__traffic_sign_type__filtering(self):
        dt_1 = get_traffic_control_device_type(code="A1")
        dt_2 = get_traffic_control_device_type(code="A2")
        get_traffic_control_device_type(code="B1")
        get_traffic_control_device_type(code="C1")

        response = self.client.get(reverse("v1:trafficcontroldevicetype-list"), data={"traffic_sign_type": "A"})

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["count"], 2)
        self.assertEqual(response_data["results"][0]["id"], str(dt_1.pk))
        self.assertEqual(response_data["results"][1]["id"], str(dt_2.pk))

    @staticmethod
    def __create_test_traffic_control_device_type():
        return TrafficControlDeviceType.objects.create(
            code="M16",
            description="Nopeusrajoitus",
        )


@pytest.mark.parametrize(
    "target_model,factory",
    (
        (DeviceTypeTargetModel.BARRIER, get_barrier_plan),
        (DeviceTypeTargetModel.BARRIER, get_barrier_real),
        (DeviceTypeTargetModel.ROAD_MARKING, get_road_marking_plan),
        (DeviceTypeTargetModel.ROAD_MARKING, get_road_marking_real),
        (DeviceTypeTargetModel.SIGNPOST, get_signpost_plan),
        (DeviceTypeTargetModel.SIGNPOST, get_signpost_real),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_traffic_light_plan),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_traffic_light_real),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_sign_plan),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_sign_real),
    ),
)
@pytest.mark.django_db
def test__device_type__target_model__valid(target_model, factory):
    client = get_api_client(user=get_user(admin=True))
    related_model = factory(device_type=get_traffic_control_device_type())
    device_type = related_model.device_type
    data = {
        "target_model": target_model.value,
    }

    response = client.patch(
        reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
        data,
        format="json",
    )

    device_type.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert device_type.target_model == target_model


@pytest.mark.parametrize(
    "target_model,factory",
    (
        (DeviceTypeTargetModel.ROAD_MARKING, get_barrier_plan),
        (DeviceTypeTargetModel.ROAD_MARKING, get_barrier_real),
        (DeviceTypeTargetModel.SIGNPOST, get_road_marking_plan),
        (DeviceTypeTargetModel.SIGNPOST, get_road_marking_real),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_signpost_plan),
        (DeviceTypeTargetModel.TRAFFIC_LIGHT, get_signpost_real),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_light_plan),
        (DeviceTypeTargetModel.TRAFFIC_SIGN, get_traffic_light_real),
        (DeviceTypeTargetModel.BARRIER, get_traffic_sign_plan),
        (DeviceTypeTargetModel.BARRIER, get_traffic_sign_real),
    ),
)
@pytest.mark.django_db
def test__device_type__target_model__invalid(target_model, factory):
    client = get_api_client(user=get_user(admin=True))
    related_model = factory(device_type=get_traffic_control_device_type())
    device_type = related_model.device_type
    data = {
        "target_model": target_model.value,
    }

    response = client.patch(
        reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}),
        data,
        format="json",
    )

    device_type.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "target_model": [
            (
                f"Some traffic control devices related to this device type instance "
                f"will become invalid if target_model value is changed to "
                f"{target_model.value}. target_model can not be changed until this "
                f"is resolved."
            ),
        ]
    }
    assert not device_type.target_model


@pytest.mark.django_db
def test__device_type__response_code_attribute():
    client = get_api_client()
    dt = get_traffic_control_device_type()

    response = client.get(reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": dt.pk}))
    response_data = response.json()

    assert "code" in response_data, (
        "Removing `code` attribute from the TrafficControlDeviceType API will break "
        "the admin traffic sign icon frontend functionality in "
        "AdminTrafficSignIconSelectWidget!"
    )


@pytest.mark.parametrize(
    ("svg_icon", "png_icon"),
    (
        ("X1.1.svg", "X1.1.svg.png"),
        ("", None),
    ),
)
@pytest.mark.django_db
def test__device_type__icons(svg_icon, png_icon):
    client = get_api_client()
    dt = get_traffic_control_device_type(code="X1.1", icon=svg_icon)
    hostname = "testserver"

    response = client.get(reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": dt.pk}))
    response_data = response.json()
    icons = response_data["icons"]
    static = settings.STATIC_URL

    if svg_icon:
        assert icons["svg"] == f"http://{hostname}{static}traffic_control/svg/traffic_sign_icons/{svg_icon}"
        assert icons["png_32"] == f"http://{hostname}{static}traffic_control/png/traffic_sign_icons/32/{png_icon}"
        assert icons["png_64"] == f"http://{hostname}{static}traffic_control/png/traffic_sign_icons/64/{png_icon}"
        assert icons["png_128"] == f"http://{hostname}{static}traffic_control/png/traffic_sign_icons/128/{png_icon}"
        assert icons["png_256"] == f"http://{hostname}{static}traffic_control/png/traffic_sign_icons/256/{png_icon}"
    else:
        assert icons is None


@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_200_OK),
        ("HEAD", status.HTTP_200_OK),
        ("OPTIONS", status.HTTP_200_OK),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__device_type__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    device_type = get_traffic_control_device_type(code="TYPE-1")
    kwargs = {"pk": device_type.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:trafficcontroldevicetype-{view_type}", kwargs=kwargs)
    data = {"code": "TYPE-2"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert TrafficControlDeviceType.objects.count() == 1
    assert TrafficControlDeviceType.objects.first().code == "TYPE-1"
    assert response.status_code == expected_status
