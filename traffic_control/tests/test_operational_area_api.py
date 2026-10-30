import json

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import OperationalArea
from traffic_control.tests.api_utils import do_illegal_geometry_test
from traffic_control.tests.factories import get_api_client, OperationalAreaFactory
from traffic_control.tests.test_base_api import illegal_multipolygon, test_multi_polygon, test_multi_polygon_2

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def test_operational_area():
    return OperationalAreaFactory()


# ==============================================================================
# Admin Tests
# ==============================================================================


@pytest.mark.django_db
def test_admin_list_operational_areas_ok(admin_api_client):
    url = reverse("v1:operationalarea-list")
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_retrieve_operational_area_ok(admin_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_create_operational_area_created(admin_api_client):
    url = reverse("v1:operationalarea-list")
    data = {"name": "TEST AREA", "location": test_multi_polygon.ewkt}
    response = admin_api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert OperationalArea.objects.filter(name="TEST AREA").count() == 1


@pytest.mark.django_db
def test_admin_update_operational_area_ok(admin_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    data = {
        "id": test_operational_area.id,
        "name": "TEST AREA",
        "location": test_multi_polygon.ewkt,
    }
    response = admin_api_client.put(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert OperationalArea.objects.filter(name="TEST AREA").count() == 1


@pytest.mark.django_db
def test_admin_delete_operational_area_deleted(admin_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    response = admin_api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert OperationalArea.objects.count() == 0


# ==============================================================================
# Regular User Tests
# ==============================================================================


@pytest.mark.django_db
def test_user_list_operational_area_forbidden(user_api_client):
    url = reverse("v1:operationalarea-list")
    response = user_api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_retrieve_operational_area_forbidden(user_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    response = user_api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_create_operational_area_forbidden(user_api_client):
    url = reverse("v1:operationalarea-list")
    data = {"name": "TEST AREA", "location": test_multi_polygon.ewkt}
    response = user_api_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_update_operational_area_forbidden(user_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    data = {
        "id": test_operational_area.id,
        "name": "TEST AREA",
        "location": test_multi_polygon.ewkt,
    }
    response = user_api_client.put(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_delete_operational_area_forbidden(user_api_client, test_operational_area):
    url = reverse("v1:operationalarea-detail", kwargs={"pk": test_operational_area.id})
    response = user_api_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# Anonymous & Geometry Tests
# ==============================================================================


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
    operational_area = OperationalAreaFactory(location=test_multi_polygon, name="Area 1")
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
        ["The location falls outside the city's boundaries."],
    )
