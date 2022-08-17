import pytest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import AdditionalSignContentPlan, AdditionalSignPlan
from traffic_control.tests.factories import (
    get_additional_sign_content_plan,
    get_additional_sign_plan,
    get_api_client,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_user,
)
from traffic_control.tests.test_base_api_3d import test_point_2_3d

# AdditionalSignPlan tests
# ===============================================


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__additional_sign_plan__list(geo_format):
    client = get_api_client()
    for owner_name in ["foo", "bar", "baz"]:
        asp = get_additional_sign_plan(owner=get_owner(name_fi=owner_name))
        get_additional_sign_content_plan(parent=asp)

    response = client.get(reverse("v1:additionalsignplan-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = AdditionalSignPlan.objects.get(pk=result["id"])
        assert result["content"][0]["id"] == str(obj.content.first().pk)

        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__additional_sign_plan__detail(geo_format):
    client = get_api_client()
    asp = get_additional_sign_plan(parent=get_traffic_sign_plan())

    response = client.get(
        reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}),
        data={"geo_format": geo_format},
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(asp.pk)
    assert response_data["parent"] == str(asp.parent.pk)

    if geo_format == "geojson":
        assert response_data["location"] == GeoJsonDict(asp.location.json)
    else:
        assert response_data["location"] == asp.location.ewkt


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_without_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request doesn't raise
    validation errors for missing content data and that the sign is created
    successfully
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
    }

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignPlan.objects.count() == 1
        assert AdditionalSignContentPlan.objects.count() == 0
        asp = AdditionalSignPlan.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignPlan.objects.count() == 0
        assert AdditionalSignContentPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request creates
    AdditionalSignContentPlan instances successfully
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type()
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {"text": "Test content 1", "order": 1, "device_type": str(dt.pk)},
            {"text": "Test content 2", "order": 2, "device_type": str(dt.pk)},
        ],
    }

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignPlan.objects.count() == 1
        asp = AdditionalSignPlan.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
        assert AdditionalSignContentPlan.objects.count() == 2
        ascp_1 = asp.content.first()
        assert ascp_1.text == "Test content 1"
        assert ascp_1.order == 1
        assert ascp_1.device_type.pk == dt.pk
        ascp_2 = asp.content.last()
        assert ascp_2.text == "Test content 2"
        assert ascp_2.order == 2
        assert ascp_2.device_type.pk == dt.pk
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignPlan.objects.count() == 0
        assert AdditionalSignContentPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_content_id(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request raises
    an error if any of the content instances have a id defined.
    Pre-existing content instances can not be assigned for newly
    created additional signs.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type()
    ascp = get_additional_sign_content_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascp.pk),
                "text": "Test content",
                "order": 1,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()
    asp = AdditionalSignPlan.objects.exclude(pk=ascp.parent.pk).first()

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
        assert not asp
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not asp
        assert AdditionalSignContentPlan.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_incomplete_data(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request raises
    validation error correctly if required data is missing.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [{"text": "Test content", "order": 1}],
    }

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"content": [{"device_type": [_("This field is required.")]}]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignPlan.objects.count() == 0
    assert AdditionalSignContentPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__update_without_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PUT request update
    is successful when content is not defined. Old content should
    be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    assert AdditionalSignContentPlan.objects.count() == 1

    response = client.put(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
        assert AdditionalSignContentPlan.objects.count() == 0
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert AdditionalSignContentPlan.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__update_with_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PUT request replaces
    AdditionalSignContentPlan instances when content does not have
    id defined. A new content instance should be created.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    original_ascp = get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [{"text": "New content", "order": 123, "device_type": str(dt.pk)}],
    }

    response = client.put(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
        new_ascp = asp.content.first()
        content = response_data["content"][0]
        assert content["id"] == str(new_ascp.pk)
        assert content["text"] == "New content"
        assert content["order"] == 123
        assert not AdditionalSignContentPlan.objects.filter(pk=original_ascp.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert asp.content.count() == 1
        original_ascp.refresh_from_db()
        assert original_ascp.parent == asp


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__update_with_content_id(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PUT request updates
    AdditionalSignContent instances successfully when id is defined.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    ascp = get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascp.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.put(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()
    ascp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
        content = response_data["content"][0]
        assert content["id"] == str(ascp.pk)
        assert content["text"] == "Updated content"
        assert content["order"] == 100
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert ascp.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__update_with_unrelated_content_id(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PUT request raises
    validation error if content is not related to the AdditionalSignPlan
    that is being updated.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    ascp = get_additional_sign_content_plan(parent=get_additional_sign_plan(location=test_point_2_3d))
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascp.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.put(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()
    ascp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            "content": [
                {"id": [("Updating content instances that do not belong to " "this additional sign is not allowed.")]}
            ]
        }
        assert ascp.parent != asp
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert ascp.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_without_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PATCH request update
    is successful when content is not defined. Old content should
    not be deleted.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    assert AdditionalSignContentPlan.objects.count() == 1

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    assert AdditionalSignContentPlan.objects.count() == 1
    assert asp.content.exists()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert AdditionalSignContentPlan.objects.count() == 1


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_with_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PATCH request replaces
    AdditionalSignContentPlan instances when content does not have
    id defined. A new content instance should be created.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    original_ascp = get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [{"text": "New content", "order": 123, "device_type": str(dt.pk)}],
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
        new_ascr = asp.content.first()
        content = response_data["content"][0]
        assert content["id"] == str(new_ascr.pk)
        assert content["text"] == "New content"
        assert content["order"] == 123
        assert not AdditionalSignContentPlan.objects.filter(pk=original_ascp.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert asp.content.count() == 1
        original_ascp.refresh_from_db()
        assert original_ascp.parent == asp


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_with_content_id(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PATCH request updates
    AdditionalSignContentPlan instances successfully when id is defined.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    ascp = get_additional_sign_content_plan(parent=asp)
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascp.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()
    ascp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
        content = response_data["content"][0]
        assert content["id"] == str(ascp.pk)
        assert content["text"] == "Updated content"
        assert content["order"] == 100
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert ascp.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_with_unrelated_content_id(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PATCH request raises
    validation error if content is not related to the parent
    AdditionalSignPlan.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    ascp = get_additional_sign_content_plan(parent=get_additional_sign_plan(location=test_point_2_3d))
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner().pk,
        "content": [
            {
                "id": str(ascp.pk),
                "text": "Updated content",
                "order": 100,
                "device_type": str(dt.pk),
            }
        ],
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()
    ascp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {
            "content": [
                {"id": [("Updating content instances that do not belong to " "this additional sign is not allowed.")]}
            ]
        }
        assert ascp.parent != asp
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]
        assert ascp.text != "Updated text"


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    asp = get_additional_sign_plan()

    response = client.delete(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        asp.refresh_from_db()
        assert not asp.is_active
        assert asp.deleted_by == user
        assert asp.deleted_at
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        asp.refresh_from_db()
        assert asp.is_active
        assert not asp.deleted_by
        assert not asp.deleted_at


@pytest.mark.django_db
def test__additional_sign_plan__soft_deleted_get_404_response():
    user = get_user()
    client = get_api_client()
    asp = get_additional_sign_plan()
    asp.soft_delete(user)

    response = client.get(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}))

    assert response.status_code == status.HTTP_404_NOT_FOUND


# AdditionalSignContentPlan tests
# ===============================================


@pytest.mark.django_db
def test__additional_sign_content_plan__list():
    client = get_api_client()
    dt = get_traffic_control_device_type(code="H17.1")
    for i in range(3):
        get_additional_sign_content_plan(order=i, device_type=dt)

    response = client.get(reverse("v1:additionalsigncontentplan-list"))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for i in range(3):
        result = response_data["results"][i]
        assert result["order"] == i
        assert result["device_type"] == str(dt.pk)


@pytest.mark.django_db
def test__additional_sign_content_plan__detail():
    user = get_user()
    client = get_api_client(user=user)
    dt = get_traffic_control_device_type(code="H17.1")
    ascp = get_additional_sign_content_plan(device_type=dt)

    response = client.get(reverse("v1:additionalsigncontentplan-detail", kwargs={"pk": ascp.pk}))
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(ascp.pk)
    assert response_data["parent"] == str(ascp.parent.pk)
    assert response_data["order"] == 1
    assert response_data["text"] == "Content"
    assert response_data["device_type"] == str(dt.pk)
    assert response_data["created_by"] == str(ascp.created_by.pk)
    assert response_data["updated_by"] == str(ascp.updated_by.pk)


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_plan__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    asp = get_additional_sign_plan()
    dt = get_traffic_control_device_type(code="H17.1")
    data = {
        "parent": str(asp.pk),
        "order": 1,
        "text": "Content",
        "device_type": str(dt.pk),
    }

    response = client.post(reverse("v1:additionalsigncontentplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignContentPlan.objects.count() == 1
        assert response_data["id"] == str(AdditionalSignContentPlan.objects.first().pk)
        assert response_data["parent"] == data["parent"]
        assert response_data["order"] == data["order"]
        assert response_data["text"] == data["text"]
        assert response_data["device_type"] == data["device_type"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignContentPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_plan__update(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    ascp = get_additional_sign_content_plan()
    dt = get_traffic_control_device_type(code="H17.1")
    data = {
        "parent": get_additional_sign_plan(owner=get_owner(name_fi="New owner")).pk,
        "text": "Updated content",
        "order": 100,
        "device_type": str(dt.pk),
    }

    response = client.put(
        reverse("v1:additionalsigncontentplan-detail", kwargs={"pk": ascp.pk}),
        data=data,
    )
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(ascp.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["text"] == data["text"]
        assert response_data["order"] == data["order"]
        assert response_data["device_type"] == str(data["device_type"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        ascp.refresh_from_db()
        assert ascp.parent.pk != data["parent"]
        assert ascp.text != data["text"]
        assert ascp.order != data["order"]
        assert ascp.device_type.pk != data["device_type"]


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_content_plan__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    ascp = get_additional_sign_content_plan()

    response = client.delete(reverse("v1:additionalsigncontentplan-detail", kwargs={"pk": ascp.pk}))

    if admin_user:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not AdditionalSignContentPlan.objects.filter(pk=ascp.pk).exists()
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignContentPlan.objects.filter(pk=ascp.pk).exists()
