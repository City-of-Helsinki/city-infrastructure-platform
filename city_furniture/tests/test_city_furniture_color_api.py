import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from city_furniture.models.common import CityFurnitureColor
from city_furniture.tests.factories import get_city_furniture_color
from traffic_control.tests.factories import get_api_client, get_user


# Read
@pytest.mark.django_db
def test__city_furniture_color__list():
    CityFurnitureColor.objects.all().delete()  # Clear colors created in migrations
    client = get_api_client()
    for name in ["foo", "bar", "baz"]:
        get_city_furniture_color(name=name)

    response = client.get(reverse("v1:cityfurniturecolor-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = CityFurnitureColor.objects.get(pk=result["id"])
        assert result["name"] == obj.name


@pytest.mark.django_db
def test__city_furniture_color__detail():
    client = get_api_client()
    obj = get_city_furniture_color()

    response = client.get(reverse("v1:cityfurniturecolor-detail", kwargs={"pk": obj.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    assert response_data["name"] == obj.name


# Create
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_color__create(admin_user):
    CityFurnitureColor.objects.all().delete()  # Clear colors created in migrations
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"name": "foo", "rgb": "#00FF00"}

    response = client.post(reverse("v1:cityfurniturecolor-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert CityFurnitureColor.objects.count() == 1
        obj = CityFurnitureColor.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["name"] == obj.name
        assert response_data["rgb"] == str(obj.rgb)
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureColor.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_color__create_with_incomplete_data(admin_user):
    """
    Test that CityFurnitureColor API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    CityFurnitureColor.objects.all().delete()  # Clear colors created in migrations
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"rgb": "#FF00FF"}

    response = client.post(reverse("v1:cityfurniturecolor-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"name": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert CityFurnitureColor.objects.count() == 0


# Update
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__city_furniture_color__update(admin_user):
    """
    Test that CityFurnitureColor API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_city_furniture_color(name="ORIGINAL_NAME")
    data = {"name": "UPDATED_NAME"}

    response = client.put(reverse("v1:cityfurniturecolor-detail", kwargs={"pk": obj.pk}), data=data)
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
def test__city_furniture_color__delete(admin_user):
    CityFurnitureColor.objects.all().delete()  # Clear colors created in migrations
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_city_furniture_color()

    response = client.delete(reverse("v1:cityfurniturecolor-detail", kwargs={"pk": obj.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CityFurnitureColor.objects.count() == 0

    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CityFurnitureColor.objects.count() == 1
