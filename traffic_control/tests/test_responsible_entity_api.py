import json

import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from traffic_control.enums import OrganizationLevel
from traffic_control.models import ResponsibleEntity
from traffic_control.tests.api_utils import do_filtering_test
from traffic_control.tests.factories import (
    get_api_client,
    get_responsible_entity_project,
    get_user,
    ResponsibleEntityFactory,
)


# Read
@pytest.mark.django_db
def test__responsible_entity__list():
    client = get_api_client()
    for name in ["foo", "bar", "baz"]:
        get_responsible_entity_project(name=name)

    response = client.get(reverse("v1:responsibleentity-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 6
    for result in response_data["results"]:
        obj = ResponsibleEntity.objects.get(pk=result["id"])
        assert result["name"] == obj.name


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (("organization_level", OrganizationLevel.SERVICE, OrganizationLevel.DIVISION),),
)
@pytest.mark.django_db
def test__responsible_entity_filtering__list(field_name, value, second_value):
    do_filtering_test(
        ResponsibleEntityFactory,
        "v1:responsibleentity-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
def test__responsible_entity__detail():
    client = get_api_client()
    obj = get_responsible_entity_project()

    response = client.get(reverse("v1:responsibleentity-detail", kwargs={"pk": obj.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    assert response_data["name"] == obj.name


# Create
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__responsible_entity__create(admin_user):
    ResponsibleEntity.objects.all().delete()  # Clear colors created in migrations
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"name": "TEST", "organization_level": OrganizationLevel.DIVISION.value}

    response = client.post(reverse("v1:responsibleentity-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert ResponsibleEntity.objects.count() == 1
        obj = ResponsibleEntity.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["name"] == obj.name
        assert response_data["organization_level"] == obj.organization_level.value
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ResponsibleEntity.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__responsible_entity__create_with_incomplete_data(admin_user):
    """
    Test that ResponsibleEntity API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"organization_level": OrganizationLevel.SERVICE.value}

    response = client.post(reverse("v1:responsibleentity-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"name": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert ResponsibleEntity.objects.count() == 0


# Update
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__responsible_entity__update(admin_user):
    """
    Test that ResponsibleEntity API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_responsible_entity_project(name="ORIGINAL_NAME")
    data = {"name": "UPDATED_NAME"}

    response = client.put(reverse("v1:responsibleentity-detail", kwargs={"pk": obj.pk}), data=data)
    response_data = response.json()
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(obj.pk)
        assert response_data["name"] == data["name"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.name == "ORIGINAL_NAME"


# Delete
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__responsible_entity__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_responsible_entity_project()

    response = client.delete(reverse("v1:responsibleentity-detail", kwargs={"pk": obj.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ResponsibleEntity.objects.count() == 3

    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ResponsibleEntity.objects.count() == 4


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
def test__responsible_entity__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    responsible_entity = get_responsible_entity_project(name="Responsible 1")
    kwargs = {"pk": responsible_entity.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:responsibleentity-{view_type}", kwargs=kwargs)
    data = {"name": "Responsible 2"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    queryset = ResponsibleEntity.objects.filter(id=responsible_entity.id)
    assert queryset.count() == 1
    assert queryset.first().name == "Responsible 1"
    assert response.status_code == expected_status
