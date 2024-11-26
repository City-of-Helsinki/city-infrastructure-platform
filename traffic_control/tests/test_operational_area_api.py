import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from traffic_control.models import OperationalArea
from traffic_control.tests.api_utils import do_illegal_geometry_test
from traffic_control.tests.factories import get_api_client, get_operational_area, get_user
from traffic_control.tests.test_base_api import illegal_multipolygon, test_multi_polygon, test_multi_polygon_2


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
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
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
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
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
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
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
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
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
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
        self.client.force_login(self.user)
        data = {
            "id": self.operational_area.id,
            "name": "TEST AREA",
            "location": test_multi_polygon.ewkt,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_operational_area_forbidden(self):
        url = reverse("v1:operationalarea-detail", kwargs={"pk": self.operational_area.id})
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# TODO: Safe methods should return OK
@pytest.mark.parametrize(
    "method, expected_status",
    (
        ("GET", status.HTTP_401_UNAUTHORIZED),
        ("HEAD", status.HTTP_401_UNAUTHORIZED),
        ("OPTIONS", status.HTTP_401_UNAUTHORIZED),
        ("POST", status.HTTP_401_UNAUTHORIZED),
        ("PUT", status.HTTP_401_UNAUTHORIZED),
        ("PATCH", status.HTTP_401_UNAUTHORIZED),
        ("DELETE", status.HTTP_401_UNAUTHORIZED),
    ),
)
@pytest.mark.parametrize("view_type", ("detail", "list"))
@pytest.mark.django_db
def test__operational_area__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized.
    """
    client = get_api_client(user=None)
    operational_area = get_operational_area(test_multi_polygon, "Area 1")
    kwargs = {"pk": operational_area.id} if view_type == "detail" else None
    resource_path = reverse(f"v1:operationalarea-{view_type}", kwargs=kwargs)
    data = {
        "location": test_multi_polygon_2.ewkt,
        "name": "Area 2",
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert OperationalArea.objects.count() == 1
    assert OperationalArea.objects.first().name == "Area 1"
    assert OperationalArea.objects.first().location.ewkt == test_multi_polygon.ewkt
    assert response.status_code == expected_status


@pytest.mark.django_db
def test__operational_area__create_with_invalid_geometry():
    data = {
        "location": illegal_multipolygon.ewkt,
        "name": "TestArea",
    }
    do_illegal_geometry_test(
        "v1:operationalarea-list",
        data,
        [f"Geometry for operationalarea {illegal_multipolygon.ewkt} is not legal"],
    )
