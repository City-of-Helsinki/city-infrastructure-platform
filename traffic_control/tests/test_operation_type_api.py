import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import OperationType
from traffic_control.tests.factories import get_api_client, get_operation_type, get_user


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__list(admin_user):
    url = reverse("v1:operationtype-list")
    client = get_api_client(user=get_user(admin=admin_user))
    response = client.get(url)
    if admin_user:
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__operation_type__detail(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ot = get_operation_type()
    url = reverse("v1:operationtype-detail", kwargs={"pk": ot.id})
    response = client.get(url)
    if admin_user:
        assert response.status_code == status.HTTP_200_OK
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


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
