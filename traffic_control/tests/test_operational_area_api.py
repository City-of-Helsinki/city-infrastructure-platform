from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import OperationalArea
from traffic_control.tests.factories import get_operational_area, get_user
from traffic_control.tests.test_base_api import test_multi_polygon


class OperationalAreaAPITestCase(APITestCase):
    def setUp(self):
        self.operational_area = get_operational_area()
        self.user = get_user()
        self.admin = get_user(admin=True)

    def test_admin_list_operational_areas_ok(self):
        url = reverse("v1:operationalarea-list")
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_retrieve_operational_area_ok(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_create_operational_area_created(self):
        url = reverse("v1:operationalarea-list")
        self.client.force_login(self.admin)
        data = {"name": "TEST AREA", "location": test_multi_polygon.ewkt}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OperationalArea.objects.filter(name="TEST AREA").count(), 1)

    def test_admin_update_operational_area_ok(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.admin)
        data = {
            "id": self.operational_area.id,
            "name": "TEST AREA",
            "location": test_multi_polygon.ewkt,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(OperationalArea.objects.filter(name="TEST AREA").count(), 1)

    def test_admin_delete_operational_area_deleted(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OperationalArea.objects.count(), 0)

    def test_user_list_operational_area_forbidden(self):
        url = reverse("v1:operationalarea-list")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_retrieve_operational_area_forbidden(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_create_operational_area_forbidden(self):
        url = reverse("v1:operationalarea-list")
        self.client.force_login(self.user)
        data = {"name": "TEST AREA", "location": test_multi_polygon.ewkt}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_operational_area_forbidden(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.user)
        data = {
            "id": self.operational_area.id,
            "name": "TEST AREA",
            "location": test_multi_polygon.ewkt,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_operational_area_forbidden(self):
        url = reverse(
            "v1:operationalarea-detail", kwargs={"pk": self.operational_area.id}
        )
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
