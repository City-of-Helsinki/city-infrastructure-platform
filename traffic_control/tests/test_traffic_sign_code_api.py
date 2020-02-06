from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import TrafficSignCode
from users.models import User


class TrafficSignCodeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="testadmin", password="testpw", email="testadmin@anders.fi"
        )
        self.client.login(username="testadmin", password="testpw")

    def test_get_all_traffic_sign_codes(self):
        """
        Ensure we can get all traffic sign code objects.
        """
        count = 3
        for i in range(count):
            TrafficSignCode.objects.create(
                code=i, description="Test description %s" % i,
            )
        response = self.client.get(reverse("api:trafficsigncode-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("count"), count)

    def test_get_traffic_sign_code_detail(self):
        """
        Ensure we can get one traffic sign code object.
        """
        traffic_sign_code = self.__create_test_traffic_sign_code()
        response = self.client.get(
            reverse("api:trafficsigncode-detail", kwargs={"pk": traffic_sign_code.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), str(traffic_sign_code.id))

    def test_create_traffic_sign_code(self):
        """
        Ensure we can create a new traffic sign code object.
        """
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.post(
            reverse("api:trafficsigncode-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TrafficSignCode.objects.count(), 1)
        traffic_sign_code = TrafficSignCode.objects.first()
        self.assertEqual(traffic_sign_code.code, data["code"])
        self.assertEqual(traffic_sign_code.description, data["description"])

    def test_create_existing_traffic_sign_code(self):
        """
        Ensure that we cannot create a new traffic sign code object with same code-value.
        """
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        self.client.post(reverse("api:trafficsigncode-list"), data, format="json")
        response = self.client.post(
            reverse("api:trafficsigncode-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TrafficSignCode.objects.count(), 1)
        traffic_sign_code = TrafficSignCode.objects.first()
        self.assertEqual(traffic_sign_code.code, data["code"])
        self.assertEqual(traffic_sign_code.description, data["description"])

    def test_update_traffic_sign_code(self):
        """
        Ensure we can update existing traffic sign code object.
        """
        traffic_sign_code = self.__create_test_traffic_sign_code()
        data = {
            "code": "L3",
            "description": "Suojatie",
        }
        response = self.client.put(
            reverse("api:trafficsigncode-detail", kwargs={"pk": traffic_sign_code.id}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TrafficSignCode.objects.count(), 1)
        traffic_sign_code = TrafficSignCode.objects.first()
        self.assertEqual(traffic_sign_code.code, data["code"])
        self.assertEqual(traffic_sign_code.description, data["description"])

    def test_delete_traffic_sign_code_detail(self):
        """
        Ensure we can delete one traffic sign code object.
        """
        traffic_sign_code = self.__create_test_traffic_sign_code()
        response = self.client.delete(
            reverse("api:trafficsigncode-detail", kwargs={"pk": traffic_sign_code.id}),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TrafficSignCode.objects.count(), 0)

    def __create_test_traffic_sign_code(self):
        return TrafficSignCode.objects.create(code="M16", description="Nopeusrajoitus",)
