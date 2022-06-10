import datetime

import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import AdditionalSignContentReal, AdditionalSignReal
from traffic_control.tests.factories import (
    add_additional_sign_real_operation,
    get_additional_sign_content_real,
    get_additional_sign_real,
    get_api_client,
    get_operation_type,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_real,
    get_user,
)
from traffic_control.tests.test_base_api_3d import test_point_2_3d

# AdditionalSignReal tests
# ===============================================


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__additional_sign_real__list(geo_format):
    client = get_api_client()
    for owner_name in ["foo", "bar", "baz"]:
        asr = get_additional_sign_real(owner=get_owner(name_fi=owner_name))
        get_additional_sign_content_real(parent=asr)

    response = client.get(reverse("v1:additionalsignreal-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = AdditionalSignReal.objects.get(pk=result["id"])
        assert result["content"][0]["id"] == str(obj.content.first().pk)

        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__additional_sign_real__detail(geo_format):
    client = get_api_client()
    asr = get_additional_sign_real()
    ascr = get_additional_sign_content_real(parent=asr)
    operation_1 = add_additional_sign_real_operation(asr, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_additional_sign_real_operation(asr, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_additional_sign_real_operation(asr, operation_date=datetime.date(2020, 11, 10))

    response = client.get(
        reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}),
        data={"geo_format": geo_format},
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(asr.pk)
    assert response_data["parent"] == str(asr.parent.pk)
    assert response_data["content"][0]["id"] == str(ascr.pk)
    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response_data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]

    if geo_format == "geojson":
        assert response_data["location"] == GeoJsonDict(asr.location.json)
    else:
        assert response_data["location"] == asr.location.ewkt


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_without_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request doesn't raise
    validation errors for missing content data and that the sign is created
    successfully
    """
    client = get_api_client(user=get_user(admin=admin_user))
    traffic_sign_real = get_traffic_sign_real()
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignReal.objects.count() == 1
        assert AdditionalSignContentReal.objects.count() == 0
        asr = AdditionalSignReal.objects.first()
        assert response_data["id"] == str(asr.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignReal.objects.count() == 0
        assert AdditionalSignContentReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request creates
    AdditionalSignContent instances successfully
    """
    client = get_api_client(user=get_user(admin=admin_user))
    traffic_sign_real = get_traffic_sign_real()
    dt = get_traffic_control_device_type()
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {"text": "Test content 1", "order": 1, "device_type": str(dt.pk)},
            {"text": "Test content 2", "order": 2, "device_type": str(dt.pk)},
        ],
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignReal.objects.count() == 1
        asr = AdditionalSignReal.objects.first()
        assert response_data["id"] == str(asr.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
        assert AdditionalSignContentReal.objects.count() == 2
        ascr_1 = asr.content.order_by("order").first()
        assert ascr_1.text == "Test content 1"
        assert ascr_1.order == 1
        assert ascr_1.device_type.pk == dt.pk
        ascr_2 = asr.content.order_by("order").last()
        assert ascr_2.text == "Test content 2"
        assert ascr_2.order == 2
        assert ascr_2.device_type.pk == dt.pk
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignReal.objects.count() == 0
        assert AdditionalSignContentReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_content_id(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request raises
    an error if any of the content instances have a id defined.
    Pre-existing content instances can not be assigned for newly
    created additional signs.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    traffic_sign_real = get_traffic_sign_real()
    dt = get_traffic_control_device_type()
    ascr = get_additional_sign_content_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascr.pk),
                "text": "Test content",
                "order": 1,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()
    asr = AdditionalSignReal.objects.exclude(pk=ascr.parent.pk).first()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            "content": [
                {
                    "id": [
                        (
                            "Creating new additional sign with pre-existing "
                            "content instance is not allowed. Content objects "
                            'must not have "id" defined.'
                        )
                    ]
                }
            ]
        }
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not asr
        assert AdditionalSignContentReal.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_incomplete_data(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    traffic_sign_real = get_traffic_sign_real()
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [{"text": "Test content", "order": 1}],
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"content": [{"device_type": [_("This field is required.")]}]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignReal.objects.count() == 0
    assert AdditionalSignContentReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__update_without_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint PUT request update
    is successful when content is not defined. Old content should
    be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    assert AdditionalSignContentReal.objects.count() == 1

    response = client.put(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
        assert AdditionalSignContentReal.objects.count() == 0
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert AdditionalSignContentReal.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__update_with_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint PUT request replaces
    AdditionalSignContentReal instances when content does not have
    id defined. A new content instance should be created.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    original_ascr = get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [{"text": "New content", "order": 123, "device_type": str(dt.pk)}],
    }

    response = client.put(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
        new_ascr = asr.content.first()
        content = response_data["content"][0]
        assert content["id"] == str(new_ascr.pk)
        assert content["text"] == "New content"
        assert content["order"] == 123
        assert not AdditionalSignContentReal.objects.filter(pk=original_ascr.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert asr.content.count() == 1
        original_ascr.refresh_from_db()
        assert original_ascr.parent == asr


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__update_with_content_id(admin_user):
    """
    Test that AdditionalSignReal API endpoint PUT request updates
    AdditionalSignContent instances successfully when id is defined.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    ascr = get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascr.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.put(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()
    ascr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
        content = response_data["content"][0]
        assert content["id"] == str(ascr.pk)
        assert content["text"] == "Updated content"
        assert content["order"] == 100
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert ascr.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__update_with_unrelated_content_id(admin_user):
    """
    Test that AdditionalSignReal API endpoint PUT request raises
    validation error if content is not related to the parent
    AdditionalSignReal.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    ascr = get_additional_sign_content_real(parent=get_additional_sign_real(location=test_point_2_3d))
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascr.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.put(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()
    ascr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            "content": [
                {"id": [("Updating content instances that do not belong to " "this additional sign is not allowed.")]}
            ]
        }
        assert ascr.parent != asr
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert ascr.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__partial_update_without_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint PATCH request update
    is successful when content is not defined. Old content should
    not be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    assert AdditionalSignContentReal.objects.count() == 1

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    assert AdditionalSignContentReal.objects.count() == 1
    assert asr.content.exists()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert AdditionalSignContentReal.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__partial_update_with_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint PATCH request replaces
    AdditionalSignContentReal instances when content does not have
    id defined. A new content instance should be created.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    original_ascr = get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [{"text": "New content", "order": 123, "device_type": str(dt.pk)}],
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
        new_ascr = asr.content.first()
        content = response_data["content"][0]
        assert content["id"] == str(new_ascr.pk)
        assert content["text"] == "New content"
        assert content["order"] == 123
        assert not AdditionalSignContentReal.objects.filter(pk=original_ascr.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert asr.content.count() == 1
        original_ascr.refresh_from_db()
        assert original_ascr.parent == asr


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__partial_update_with_content_id(admin_user):
    """
    Test that AdditionalSignReal API endpoint PATCH request updates
    AdditionalSignContent instances successfully when id is defined.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    ascr = get_additional_sign_content_real(parent=asr)
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascr.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()
    ascr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
        content = response_data["content"][0]
        assert content["id"] == str(ascr.pk)
        assert content["text"] == "Updated content"
        assert content["order"] == 100
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert ascr.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__partial_update_with_unrelated_content_id(admin_user):
    """
    Test that AdditionalSignReal API endpoint PATCH request raises
    validation error if content is not related to the parent
    AdditionalSignReal.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asr = get_additional_sign_real()
    ascr = get_additional_sign_content_real(parent=get_additional_sign_real(location=test_point_2_3d))
    traffic_sign_real = get_traffic_sign_real(device_type=dt)
    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascr.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()
    ascr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            "content": [
                {"id": [("Updating content instances that do not belong to " "this additional sign is not allowed.")]}
            ]
        }
        assert ascr.parent != asr
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]
        assert ascr.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    asr = get_additional_sign_real()

    response = client.delete(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        asr.refresh_from_db()
        assert not asr.is_active
        assert asr.deleted_by == user
        assert asr.deleted_at
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        asr.refresh_from_db()
        assert asr.is_active
        assert not asr.deleted_by
        assert not asr.deleted_at


@pytest.mark.django_db
def test__additional_sign_real__soft_deleted_get_404_response():
    user = get_user()
    client = get_api_client()
    asr = get_additional_sign_real()
    asr.soft_delete(user)

    response = client.get(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


# AdditionalSignContentReal tests
# ===============================================


@pytest.mark.django_db
def test__additional_sign_content_real__list():
    client = get_api_client()
    dt = get_traffic_control_device_type(code="H17.1")
    for i in range(3):
        get_additional_sign_content_real(order=i, device_type=dt)

    response = client.get(reverse("v1:additionalsigncontentreal-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for i in range(3):
        result = response_data["results"][i]
        assert result["order"] == i
        assert result["device_type"] == str(dt.pk)


@pytest.mark.django_db
def test__additional_sign_content_real__detail():
    user = get_user()
    client = get_api_client(user)
    dt = get_traffic_control_device_type(code="H17.1")
    ascr = get_additional_sign_content_real(device_type=dt)

    response = client.get(reverse("v1:additionalsigncontentreal-detail", kwargs={"pk": ascr.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(ascr.pk)
    assert response_data["parent"] == str(ascr.parent.pk)
    assert response_data["order"] == 1
    assert response_data["text"] == "Content"
    assert response_data["device_type"] == str(dt.pk)
    assert response_data["created_by"] == str(ascr.created_by.pk)
    assert response_data["updated_by"] == str(ascr.updated_by.pk)


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_real__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    asr = get_additional_sign_real()
    dt = get_traffic_control_device_type(code="H17.1")
    data = {
        "parent": str(asr.pk),
        "order": 1,
        "text": "Content",
        "device_type": str(dt.pk),
    }

    response = client.post(reverse("v1:additionalsigncontentreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignContentReal.objects.count() == 1
        assert response_data["id"] == str(AdditionalSignContentReal.objects.first().pk)
        assert response_data["parent"] == data["parent"]
        assert response_data["order"] == data["order"]
        assert response_data["text"] == data["text"]
        assert response_data["device_type"] == data["device_type"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignContentReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_real__update(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ascr = get_additional_sign_content_real()
    dt = get_traffic_control_device_type(code="H17.1")
    data = {
        "parent": get_additional_sign_real(owner=get_owner(name_fi="New owner")).pk,
        "text": "Updated content",
        "order": 100,
        "device_type": str(dt.pk),
    }

    response = client.put(
        reverse("v1:additionalsigncontentreal-detail", kwargs={"pk": ascr.pk}),
        data=data,
    )
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ascr.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["text"] == data["text"]
        assert response_data["order"] == data["order"]
        assert response_data["device_type"] == str(data["device_type"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        ascr.refresh_from_db()
        assert ascr.parent.pk != data["parent"]
        assert ascr.text != data["text"]
        assert ascr.order != data["order"]
        assert ascr.device_type.pk != data["device_type"]


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_real__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    ascr = get_additional_sign_content_real()

    response = client.delete(reverse("v1:additionalsigncontentreal-detail", kwargs={"pk": ascr.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AdditionalSignContentReal.objects.filter(pk=ascr.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignContentReal.objects.filter(pk=ascr.pk).exists()


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real_operation__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    asr = get_additional_sign_real()
    operation_type = get_operation_type()
    data = {"operation_date": "2020-01-01", "operation_type_id": operation_type.pk}
    url = reverse("additional-sign-real-operations-list", kwargs={"additional_sign_real_pk": asr.pk})
    response = client.post(url, data, format="json")

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert asr.operations.all().count() == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.operations.all().count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real_operation__update(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    asr = get_additional_sign_real()
    operation_type = get_operation_type()
    operation = add_additional_sign_real_operation(
        additional_sign_real=asr, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}
    url = reverse(
        "additional-sign-real-operations-detail",
        kwargs={"additional_sign_real_pk": asr.pk, "pk": operation.pk},
    )
    response = client.put(url, data, format="json")

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert asr.operations.all().count() == 1
        assert asr.operations.all().first().operation_date == datetime.date(2020, 2, 1)
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.operations.all().count() == 1
        assert asr.operations.all().first().operation_date == datetime.date(2020, 1, 1)
