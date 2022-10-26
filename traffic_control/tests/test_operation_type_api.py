import json

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import OperationType
from traffic_control.tests.factories import get_api_client, get_operation_type, get_user


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__list(admin_user):
    ot = get_operation_type()
    url = reverse("v1:operationtype-list")
    client = get_api_client(user=get_user(admin=admin_user))
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == ot.id
    assert response.data["results"][0]["name"] == ot.name


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__detail(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ot = get_operation_type()
    url = reverse("v1:operationtype-detail", kwargs={"pk": ot.id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == ot.id
    assert response.data["name"] == ot.name


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    url = reverse("v1:operationtype-list")
    data = {
        "name": "Test operation type",
        "traffic_sign": True,
        "additional_sign": True,
        "road_marking": True,
        "barrier": True,
        "signpost": True,
        "traffic_light": True,
        "mount": True,
    }
    response = client.post(url, data)
    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert OperationType.objects.all().count() == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert OperationType.objects.all().count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__update(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ot = get_operation_type()
    url = reverse("v1:operationtype-detail", kwargs={"pk": ot.id})
    data = {
        "name": "UPDATED OPERATION TYPE",
        "traffic_sign": True,
        "additional_sign": True,
        "road_marking": True,
        "barrier": True,
        "signpost": True,
        "traffic_light": True,
        "mount": True,
    }
    response = client.put(url, data)
    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "UPDATED OPERATION TYPE"
        assert OperationType.objects.all().count() == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert OperationType.objects.all().count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__delete(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ot = get_operation_type()
    url = reverse("v1:operationtype-detail", kwargs={"pk": ot.id})
    response = client.delete(url)
    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert OperationType.objects.all().count() == 0
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert OperationType.objects.all().count() == 1


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
def test__operation_type__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    operation_type = get_operation_type(name="Oper1")
    kwargs = {"pk": operation_type.id} if view_type == "detail" else None
    resource_path = reverse(f"v1:operationtype-{view_type}", kwargs=kwargs)
    data = {"name": "Oper2"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert OperationType.objects.count() == 1
    assert OperationType.objects.first().name == "Oper1"
    assert response.status_code == expected_status
