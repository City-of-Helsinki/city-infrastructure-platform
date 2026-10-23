import json

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import PortalType
from traffic_control.tests.factories import get_api_client, get_portal_type

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def test_portal_type():
    return PortalType.objects.create(
        structure="Test structure",
        build_type="Test build type",
        model="Test model",
    )


# ==============================================================================
# PortalType API Tests
# ==============================================================================


@pytest.mark.django_db
def test__list__as_user__ok(user_api_client):
    """
    Ensure that user can get list of portal type objects.
    """
    count = 3
    for i in range(count):
        PortalType.objects.create(structure="Test structure", build_type="Test build type", model=i)
    response = user_api_client.get(reverse("v1:portaltype-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count


@pytest.mark.django_db
def test__get_list__as_admin__ok(admin_api_client):
    """
    Ensure that admin can get list of portal type objects.
    """
    count = 3
    for i in range(count):
        PortalType.objects.create(structure="Test structure", build_type="Test build type", model=i)
    response = admin_api_client.get(reverse("v1:portaltype-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count


@pytest.mark.django_db
def test__retrieve__as_user__ok(user_api_client, test_portal_type):
    """
    Ensure that user can get portal type object.
    """
    response = user_api_client.get(reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(test_portal_type.id)


@pytest.mark.django_db
def test__retrieve__as_admin__ok(admin_api_client, test_portal_type):
    """
    Ensure that admin can get portal type object.
    """
    response = admin_api_client.get(reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(test_portal_type.id)


@pytest.mark.django_db
def test__create__as_user__forbidden(user_api_client):
    """
    Ensure that user cannot create a new portal type object.
    """
    data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
    response = user_api_client.post(reverse("v1:portaltype-list"), data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert PortalType.objects.count() == 0


@pytest.mark.django_db
def test__create__as_admin__created(admin_api_client):
    """
    Ensure that admin can create a new portal type object.
    """
    data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
    response = admin_api_client.post(reverse("v1:portaltype-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert PortalType.objects.count() == 1
    portal_type = PortalType.objects.first()
    assert portal_type.structure == data["structure"]
    assert portal_type.build_type == data["build_type"]
    assert portal_type.model == data["model"]


@pytest.mark.django_db
def test__create_existing__bad_request(admin_api_client):
    """
    Ensure that API will not create a new portal type object with same values.
    """
    data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
    response = admin_api_client.post(reverse("v1:portaltype-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    response = admin_api_client.post(reverse("v1:portaltype-list"), data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert PortalType.objects.count() == 1
    portal_type = PortalType.objects.first()
    assert portal_type.structure == data["structure"]
    assert portal_type.build_type == data["build_type"]
    assert portal_type.model == data["model"]


@pytest.mark.django_db
def test__update__as_user__forbidden(user_api_client, test_portal_type):
    """
    Ensure that user cannot update existing portal type object.
    """
    data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
    response = user_api_client.put(
        reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test__update__as_admin__ok(admin_api_client, test_portal_type):
    """
    Ensure that admin can update existing portal type object.
    """
    data = {"structure": "Putki", "build_type": "kehä", "model": "tyyppi I"}
    response = admin_api_client.put(
        reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert PortalType.objects.count() == 1
    portal_type = PortalType.objects.first()
    assert portal_type.structure == data["structure"]
    assert portal_type.build_type == data["build_type"]
    assert portal_type.model == data["model"]


@pytest.mark.django_db
def test__destroy__as_user__forbidden(user_api_client, test_portal_type):
    """
    Ensure that user cannot destroy portal type object.
    """
    response = user_api_client.delete(
        reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert PortalType.objects.count() == 1


@pytest.mark.django_db
def test__destroy__as_admin__success(admin_api_client, test_portal_type):
    """
    Ensure that admin can delete portal type object.
    """
    response = admin_api_client.delete(
        reverse("v1:portaltype-detail", kwargs={"pk": test_portal_type.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert PortalType.objects.count() == 0


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
def test__portal_type__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    portal_type = get_portal_type(
        model="Model 1",
        build_type="Build type 1",
        structure="Structure 1",
    )
    kwargs = {"pk": portal_type.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:portaltype-{view_type}", kwargs=kwargs)
    data = {
        "structure": "Structure 2",
        "build_type": "Build type 2",
        "model": "Model 2",
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert PortalType.objects.count() == 1
    assert PortalType.objects.first().model == "Model 1"
    assert response.status_code == expected_status
