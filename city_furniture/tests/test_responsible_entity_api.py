import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from city_furniture.enums import OrganizationLevel
from city_furniture.models.common import ResponsibleEntity
from city_furniture.tests.factories import get_responsible_entity
from traffic_control.tests.factories import get_api_client, get_user


# Read
@pytest.mark.django_db
def test__responsible_entity__list():
    client = get_api_client()
    for name in ["foo", "bar", "baz"]:
        get_responsible_entity(name=name)

    response = client.get(reverse("v1:responsibleentity-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 7
    for result in response_data["results"]:
        obj = ResponsibleEntity.objects.get(pk=result["id"])
        assert result["name"] == obj.name


@pytest.mark.django_db
def test__responsible_entity__detail():
    client = get_api_client()
    obj = get_responsible_entity()

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
    obj = get_responsible_entity(name="ORIGINAL_NAME")
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
    obj = get_responsible_entity()

    response = client.delete(reverse("v1:responsibleentity-detail", kwargs={"pk": obj.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ResponsibleEntity.objects.count() == 4

    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ResponsibleEntity.objects.count() == 5
