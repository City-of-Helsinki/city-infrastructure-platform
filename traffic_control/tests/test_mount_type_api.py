import json

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import MountType
from traffic_control.tests.factories import get_api_client, get_mount_type

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def test_mount_type():
    return MountType.objects.create(code="POST", description="Post")


# ==============================================================================
# MountType API Tests
# ==============================================================================


@pytest.mark.django_db
def test__list__as_user__ok(user_api_client):
    types = ["post", "wall", "wire"]
    for t in types:
        MountType.objects.create(code=t.upper(), description=t.capitalize())
    response = user_api_client.get(reverse("v1:mounttype-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == len(types)


@pytest.mark.django_db
def test__get_list__as_admin__ok(admin_api_client):
    types = ["post", "wall", "wire"]
    for t in types:
        MountType.objects.create(code=t.upper(), description=t.capitalize())
    response = admin_api_client.get(reverse("v1:mounttype-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == len(types)


@pytest.mark.django_db
def test__retrieve__as_user__ok(user_api_client, test_mount_type):
    response = user_api_client.get(reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(test_mount_type.id)


@pytest.mark.django_db
def test__retrieve__as_admin__ok(admin_api_client, test_mount_type):
    response = admin_api_client.get(reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(test_mount_type.id)


@pytest.mark.django_db
def test__create__as_user__forbidden(user_api_client):
    data = {"code": "POST", "description": "Post"}
    response = user_api_client.post(reverse("v1:mounttype-list"), data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert MountType.objects.count() == 0


@pytest.mark.django_db
def test__create__as_admin__created(admin_api_client):
    data = {"code": "POST", "description": "Post"}
    response = admin_api_client.post(reverse("v1:mounttype-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert MountType.objects.count() == 1
    mount_type = MountType.objects.first()
    assert mount_type.code == data["code"]
    assert mount_type.description == data["description"]
    assert mount_type.digiroad_code is None
    assert mount_type.digiroad_description == ""


@pytest.mark.django_db
def test__update__as_user__forbidden(user_api_client, test_mount_type):
    data = {"code": "POST", "description": "Post"}
    response = user_api_client.put(
        reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test__update__as_admin__ok(admin_api_client, test_mount_type):
    data = {"code": "POST", "description": "Post"}
    response = admin_api_client.put(
        reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert MountType.objects.count() == 1
    mount_type = MountType.objects.first()
    assert mount_type.code == data["code"]
    assert mount_type.description == data["description"]


@pytest.mark.django_db
def test__destroy__as_user__forbidden(user_api_client, test_mount_type):
    response = user_api_client.delete(
        reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert MountType.objects.count() == 1


@pytest.mark.django_db
def test__destroy__as_admin__success(admin_api_client, test_mount_type):
    response = admin_api_client.delete(
        reverse("v1:mounttype-detail", kwargs={"pk": test_mount_type.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert MountType.objects.count() == 0


# ==============================================================================
# Anonymous User Tests
# ==============================================================================


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
def test__mount_type__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    mount_type = get_mount_type(code="TYPE-1")
    kwargs = {"pk": mount_type.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:mounttype-{view_type}", kwargs=kwargs)
    data = {"code": "TYPE-2", "description": ""}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert MountType.objects.count() == 1
    assert MountType.objects.first().code == "TYPE-1"
    assert response.status_code == expected_status
