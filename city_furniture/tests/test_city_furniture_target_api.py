import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from city_furniture.models.common import CityFurnitureTarget
from city_furniture.tests.factories import get_city_furniture_target
from traffic_control.tests.factories import get_api_client, get_user


# Read
@pytest.mark.django_db
def test__city_furniture_target__list():
    client = get_api_client()
    for name_fi in ["foo", "bar", "baz"]:
        get_city_furniture_target(name_fi=name_fi)

    response = client.get(reverse("v1:cityfurnituretarget-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = CityFurnitureTarget.objects.get(pk=result["id"])
        assert result["name_fi"] == obj.name_fi


@pytest.mark.django_db
def test__city_furniture_target__detail():
    client = get_api_client()
    obj = get_city_furniture_target()

    response = client.get(reverse("v1:cityfurnituretarget-detail", kwargs={"pk": obj.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    assert response_data["name_fi"] == obj.name_fi


# Create
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_target__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    data = {
        "name_fi": "foo",
        "name_sw": "bar",
        "name_en": "baz",
        "description": None,
        "source_id": None,
        "source_name": None,
    }

    response = client.post(reverse("v1:cityfurnituretarget-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert CityFurnitureTarget.objects.count() == 1
        obj = CityFurnitureTarget.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["name_fi"] == data["name_fi"]
        assert response_data["name_sw"] == data["name_sw"]
        assert response_data["name_en"] == data["name_en"]
        assert response_data["description"] == data["description"]
        assert response_data["source_id"] == data["source_id"]
        assert response_data["source_name"] == data["source_name"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureTarget.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_target__create_with_incomplete_data(admin_user):
    """
    Test that CityFurnitureTarget API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    data = {
        "name_sw": "bar",
        "name_en": "baz",
    }

    response = client.post(reverse("v1:cityfurnituretarget-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"name_fi": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert CityFurnitureTarget.objects.count() == 0


# Update
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_target__update(admin_user):
    """
    Test that CityFurnitureTarget API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_city_furniture_target(name_fi="ORIGINAL_NAME")
    data = {"name_fi": "UPDATED_NAME"}

    response = client.put(reverse("v1:cityfurnituretarget-detail", kwargs={"pk": obj.pk}), data=data)
    response_data = response.json()
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(obj.pk)
        assert response_data["name_fi"] == data["name_fi"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.name_fi == "ORIGINAL_NAME"


# Delete
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_target__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_city_furniture_target()

    response = client.delete(reverse("v1:cityfurnituretarget-detail", kwargs={"pk": obj.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CityFurnitureTarget.objects.count() == 0

    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureTarget.objects.count() == 1
