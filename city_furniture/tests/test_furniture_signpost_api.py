import datetime

import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.tests.factories import (
    add_furniture_signpost_real_operation,
    get_city_furniture_device_type,
    get_furniture_signpost_plan,
    get_furniture_signpost_real,
)
from traffic_control.tests.factories import get_api_client, get_operation_type, get_owner, get_user
from traffic_control.tests.test_base_api_3d import test_point_2_3d, test_point_3d


# Read
@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__furniture_signpost_plan__list(geo_format):
    client = get_api_client()
    for owner_name in ["foo", "bar", "baz"]:
        get_furniture_signpost_plan(owner=get_owner(name_fi=owner_name))

    response = client.get(reverse("v1:furnituresignpostplan-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = FurnitureSignpostPlan.objects.get(pk=result["id"])
        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__furniture_signpost_real__list(geo_format):
    client = get_api_client()
    for owner_name in ["foo", "bar", "baz"]:
        get_furniture_signpost_real(owner=get_owner(name_fi=owner_name))

    response = client.get(reverse("v1:furnituresignpostreal-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = FurnitureSignpostReal.objects.get(pk=result["id"])
        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__furniture_signpost_plan__detail(geo_format):
    client = get_api_client()
    obj = get_furniture_signpost_plan()

    response = client.get(
        reverse("v1:furnituresignpostplan-detail", kwargs={"pk": obj.pk}),
        data={"geo_format": geo_format},
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    if geo_format == "geojson":
        assert response_data["location"] == GeoJsonDict(obj.location.json)
    else:
        assert response_data["location"] == obj.location.ewkt


@pytest.mark.django_db
@pytest.mark.parametrize("geo_format", ("", "geojson"))
def test__furniture_signpost_real__detail(geo_format):
    client = get_api_client()
    obj = get_furniture_signpost_real()
    operation_1 = add_furniture_signpost_real_operation(obj, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_furniture_signpost_real_operation(obj, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_furniture_signpost_real_operation(obj, operation_date=datetime.date(2020, 11, 10))

    response = client.get(
        reverse("v1:furnituresignpostreal-detail", kwargs={"pk": obj.pk}),
        data={"geo_format": geo_format},
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(obj.pk)
    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response_data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]
    if geo_format == "geojson":
        assert response_data["location"] == GeoJsonDict(obj.location.json)
    else:
        assert response_data["location"] == obj.location.ewkt


# Create
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_plan__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"location": str(test_point_3d), "owner": get_owner().pk, "device_type": get_city_furniture_device_type().pk}

    response = client.post(reverse("v1:furnituresignpostplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert FurnitureSignpostPlan.objects.count() == 1
        obj = FurnitureSignpostPlan.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FurnitureSignpostPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"location": str(test_point_3d), "owner": get_owner().pk, "device_type": get_city_furniture_device_type().pk}

    response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert FurnitureSignpostReal.objects.count() == 1
        obj = FurnitureSignpostReal.objects.first()
        assert response_data["id"] == str(obj.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FurnitureSignpostReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_plan__create_with_incomplete_data(admin_user):
    """
    Test that FurnitureSignpostPlan API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"location": str(test_point_3d), "owner": get_owner().pk}

    response = client.post(reverse("v1:furnituresignpostplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"device_type": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert FurnitureSignpostPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__create_with_incomplete_data(admin_user):
    """
    Test that FurnitureSignpostReal API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    data = {"location": str(test_point_3d), "owner": get_owner().pk}

    response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"device_type": [_("This field is required.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert FurnitureSignpostReal.objects.count() == 0


# Update
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_plan__update(admin_user):
    """
    Test that FurnitureSignpostPlan API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_furniture_signpost_plan()
    cfdt = get_city_furniture_device_type(code="TEST_CODE_2")
    data = {
        "owner": get_owner().pk,
        "location": str(test_point_2_3d),
        "device_type": cfdt.pk,
    }

    response = client.put(reverse("v1:furnituresignpostplan-detail", kwargs={"pk": obj.pk}), data=data)
    response_data = response.json()
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(obj.pk)
        assert response_data["device_type"] == str(cfdt.pk)
        assert response_data["location"] == obj.location.ewkt
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__update(admin_user):
    """
    Test that FurnitureSignpostReal API endpoint PUT request update
    is successful when content is not defined. Old content should be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_furniture_signpost_real()
    cfdt = get_city_furniture_device_type(code="TEST_CODE_2")
    data = {
        "owner": get_owner().pk,
        "location": str(test_point_2_3d),
        "device_type": cfdt.pk,
        "installation_date": "2022-02-07",
        "value": 42,
    }

    response = client.put(reverse("v1:furnituresignpostreal-detail", kwargs={"pk": obj.pk}), data=data)
    response_data = response.json()
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(obj.pk)
        assert response_data["installation_date"] == obj.installation_date.strftime("%Y-%m-%d")
        assert response_data["device_type"] == str(cfdt.pk)
        assert response_data["location"] == obj.location.ewkt
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.value is None


# Delete
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_plan__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_furniture_signpost_plan()

    response = client.delete(reverse("v1:furnituresignpostplan-detail", kwargs={"pk": obj.pk}))
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not obj.is_active
        assert obj.deleted_by == user
        assert obj.deleted_at
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.is_active
        assert not obj.deleted_by
        assert not obj.deleted_at


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    obj = get_furniture_signpost_real()

    response = client.delete(reverse("v1:furnituresignpostreal-detail", kwargs={"pk": obj.pk}))
    obj.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not obj.is_active
        assert obj.deleted_by == user
        assert obj.deleted_at
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.is_active
        assert not obj.deleted_by
        assert not obj.deleted_at


@pytest.mark.django_db
def test__furniture_signpost_plan__soft_deleted_get_404_response():
    user = get_user()
    client = get_api_client()
    obj = get_furniture_signpost_plan()
    obj.soft_delete(user)

    response = client.get(reverse("v1:furnituresignpostplan-detail", kwargs={"pk": obj.pk}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test__furniture_signpost_real__soft_deleted_get_404_response():
    user = get_user()
    client = get_api_client()
    obj = get_furniture_signpost_real()
    obj.soft_delete(user)

    response = client.get(reverse("v1:furnituresignpostreal-detail", kwargs={"pk": obj.pk}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Operations
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real_operation__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_furniture_signpost_real()
    operation_type = get_operation_type()
    data = {"operation_date": "2020-01-01", "operation_type_id": operation_type.pk}
    url = reverse("furniture-signpost-real-operations-list", kwargs={"furniture_signpost_real_pk": obj.pk})
    response = client.post(url, data, format="json")

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert obj.operations.all().count() == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.operations.all().count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real_operation__update(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    obj = get_furniture_signpost_real()
    operation_type = get_operation_type()
    operation = add_furniture_signpost_real_operation(
        furniture_signpost_real=obj, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}
    url = reverse(
        "furniture-signpost-real-operations-detail",
        kwargs={"furniture_signpost_real_pk": obj.pk, "pk": operation.pk},
    )
    response = client.put(url, data, format="json")

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert obj.operations.all().count() == 1
        assert obj.operations.all().first().operation_date == datetime.date(2020, 2, 1)
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert obj.operations.all().count() == 1
        assert obj.operations.all().first().operation_date == datetime.date(2020, 1, 1)
