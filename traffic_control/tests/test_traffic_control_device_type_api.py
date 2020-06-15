from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import TrafficControlDeviceType
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
                code=i, description="Test description %s" % i,
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
                code=i, description="Test description %s" % i,
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
        response = self.client.get(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(device_type.id))

    def test__retrieve__as_admin__ok(self):
        """
        Ensure that admin can get one traffic control device type object.
        """
        self.client.force_login(self.admin_user)
        device_type = self.__create_test_traffic_control_device_type()
        response = self.client.get(
            reverse("v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id})
        )
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
        response = self.client.post(
            reverse("v1:trafficcontroldevicetype-list"), data, format="json"
        )
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
        }
        response = self.client.post(
            reverse("v1:trafficcontroldevicetype-list"), data, format="json"
        )
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
        response = self.client.post(
            reverse("v1:trafficcontroldevicetype-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            reverse("v1:trafficcontroldevicetype-list"), data, format="json"
        )
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
            reverse(
                "v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}
            ),
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
            reverse(
                "v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}
            ),
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
            reverse(
                "v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}
            ),
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
            reverse(
                "v1:trafficcontroldevicetype-detail", kwargs={"pk": device_type.id}
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficControlDeviceType.objects.count(), 0)

    @staticmethod
    def __create_test_traffic_control_device_type():
        return TrafficControlDeviceType.objects.create(
            code="M16", description="Nopeusrajoitus",
        )
