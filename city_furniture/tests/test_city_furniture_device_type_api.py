import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from city_furniture.models.common import CityFurnitureDeviceType
from city_furniture.tests.factories import get_city_furniture_device_type
from traffic_control.tests.factories import get_api_client, get_user


# Read
@pytest.mark.django_db
def test__city_furniture_device_type__list():
    client = get_api_client()
    for code in ["foo", "bar", "baz"]:
        get_city_furniture_device_type(code=code)

    response = client.get(reverse("v1:cityfurnituredevicetype-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = CityFurnitureDeviceType.objects.get(pk=result["id"])
        assert result["code"] == obj.code


@pytest.mark.django_db
def test__city_furniture_device_type__detail():
    client = get_api_client()
    obj = get_city_furniture_device_type()

    response = client.get(reverse("v1:cityfurnituredevicetype-detail", kwargs={"pk": obj.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    assert response_data["code"] == obj.code


# Create
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_device_type__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"code": "TEST_CODE", "class_type": "1030", "function_type": "1090", "target_model": None}

    response = client.post(reverse("v1:cityfurnituredevicetype-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert CityFurnitureDeviceType.objects.count() == 1
        obj = CityFurnitureDeviceType.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["code"] == data["code"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureDeviceType.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_device_type__create_with_incomplete_data(admin_user):
    """
    Test that CityFurnitureDeviceType API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"class_type": "1030", "function_type": "1090", "target_model": None}

    response = client.post(reverse("v1:cityfurnituredevicetype-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"code": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert CityFurnitureDeviceType.objects.count() == 0


# Update
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_device_type__update(admin_user):
    """
    Test that CityFurnitureDeviceType API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_city_furniture_device_type(code="TEST_CODE")
    data = {"code": "TEST_CODE_2", "class_type": "1000", "function_type": "1000"}

    response = client.put(reverse("v1:cityfurnituredevicetype-detail", kwargs={"pk": obj.pk}), data=data)
    response_data = response.json()
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(obj.pk)
        assert response_data["code"] == data["code"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.code == "TEST_CODE"


# Delete
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_device_type__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_city_furniture_device_type()

    response = client.delete(reverse("v1:cityfurnituredevicetype-detail", kwargs={"pk": obj.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CityFurnitureDeviceType.objects.count() == 0

    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureDeviceType.objects.count() == 1
