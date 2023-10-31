import json

import pytest
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.models import AdditionalSignPlan
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_api_client,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_plan,
    get_user,
)
from traffic_control.tests.models.test_traffic_control_device_type import (
    another_content_valid_by_simple_schema,
    content_invalid_by_simple_schema,
    content_invalid_by_simple_schema_2,
    content_valid_by_simple_schema,
    content_valid_by_simple_schema_2,
    simple_schema,
    simple_schema_2,
)

# AdditionalSignPlan tests
# ===============================================


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.django_db
def test__additional_sign_plan__list(geo_format):
    client = get_api_client()
    for owner_name in ["foo", "bar", "baz"]:
        get_additional_sign_plan(owner=get_owner(name_fi=owner_name))

    response = client.get(reverse("v1:additionalsignplan-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = AdditionalSignPlan.objects.get(pk=result["id"])
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
        asp = AdditionalSignPlan.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request creates
    an AdditionalSignPlan with content_s.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content_valid_by_simple_schema,
    }

    assert AdditionalSignPlan.objects.count() == 0

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignPlan.objects.count() == 1
        asp = AdditionalSignPlan.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
        assert response_data["device_type"] == str(data["device_type"])
        assert response_data["content_s"] == data["content_s"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignPlan.objects.count() == 0


@pytest.mark.parametrize(
    "schema,content",
    (
        (None, simple_schema),
        (simple_schema, content_invalid_by_simple_schema),
    ),
)
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_content_invalid(schema, content, admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST doesn't create
    an AdditionalSignPlan when content_s is invalid to device type's content_schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content,
    }

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response_data["content_s"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignPlan.objects.count() == 0


old_schemas_and_contents = (
    (None, None),
    (simple_schema, content_valid_by_simple_schema),
    (simple_schema_2, content_valid_by_simple_schema_2),
)

new_schemas_and_contents_and_expectations = (
    (None, None, True),
    (simple_schema, content_valid_by_simple_schema, True),
    (simple_schema_2, content_valid_by_simple_schema_2, True),
    (simple_schema, content_invalid_by_simple_schema, False),
    (simple_schema_2, content_invalid_by_simple_schema_2, False),
)


@pytest.mark.parametrize("old_schema,old_content", old_schemas_and_contents)
@pytest.mark.parametrize("new_schema,new_content,expect_valid", new_schemas_and_contents_and_expectations)
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__update_device_type_and_content(
    old_schema,
    old_content,
    new_schema,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignPlan API endpoint PUT request update
    is successful when changing both device_type and content_s, but is
    not successful when structured content doesn't match device type's content_schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    old_dt = get_traffic_control_device_type(code="A1234", content_schema=old_schema)
    new_dt = get_traffic_control_device_type(code="new_code", content_schema=new_schema)
    tsp = get_traffic_sign_plan()
    asp = get_additional_sign_plan(content_s=old_content, device_type=old_dt)

    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner(name_en="New owner").pk,
        "device_type": new_dt.id,
        "content_s": new_content,
    }

    response = client.put(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == str(asp.pk)
            assert response_data["owner"] == str(data["owner"])
            assert response_data["device_type"] == str(data["device_type"])
            assert response_data["content_s"] == data["content_s"]
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner.pk != data["owner"]
        assert asp.device_type != data["device_type"]

        if old_content == new_content:
            assert asp.content_s == data["content_s"]
        else:
            assert asp.content_s != data["content_s"]


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_without_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint PATCH request update
    is successful.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="A1234")
    asp = get_additional_sign_plan()
    tsp = get_traffic_sign_plan(device_type=dt)
    data = {
        "parent": tsp.pk,
        "location": str(tsp.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp.pk}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asp.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.owner != data["owner"]


@pytest.mark.parametrize(
    "schema,old_content,new_content,expect_valid",
    (
        (None, None, None, True),
        (simple_schema, content_valid_by_simple_schema, another_content_valid_by_simple_schema, True),
        (simple_schema, content_valid_by_simple_schema, content_invalid_by_simple_schema, False),
        (None, None, content_valid_by_simple_schema, False),
    ),
)
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_content(
    schema,
    old_content,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignPlan API endpoint PATCH request updates
    structured content when it's valid according to device type's content schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = get_traffic_control_device_type(code="DT1", content_schema=schema)
    asp = get_additional_sign_plan(device_type=dt, content_s=old_content)
    asp_id = str(asp.pk)
    data = {
        "content_s": new_content,
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp_id}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == asp_id
            assert response_data["content_s"] == new_content
            assert response_data["device_type"] == str(dt.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
            assert asp.content_s == old_content
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.content_s == old_content


@pytest.mark.parametrize(
    "old_schema,old_content",
    (
        (None, None),
        (simple_schema, content_valid_by_simple_schema),
        (simple_schema, another_content_valid_by_simple_schema),
        (simple_schema_2, content_valid_by_simple_schema_2),
    ),
)
@pytest.mark.parametrize(
    "new_schema,new_content,expect_valid",
    (
        (None, None, True),
        (simple_schema, content_valid_by_simple_schema, True),
        (None, content_valid_by_simple_schema, False),
        (simple_schema, None, False),
    ),
)
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__partial_update_device_type_and_content(
    old_schema,
    new_schema,
    old_content,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignPlan API endpoint PATCH request updates structured
    content and device type when content is valid according to device type's content schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    old_dt = get_traffic_control_device_type(code="DT1", content_schema=old_schema)
    new_dt = get_traffic_control_device_type(code="DT2", content_schema=new_schema)
    asp = get_additional_sign_plan(device_type=old_dt, content_s=old_content)
    asp_id = str(asp.pk)
    data = {
        "content_s": new_content,
        "device_type": str(new_dt.id),
    }

    response = client.patch(reverse("v1:additionalsignplan-detail", kwargs={"pk": asp_id}), data=data)
    response_data = response.json()
    asp.refresh_from_db()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == asp_id
            assert response_data["content_s"] == new_content
            assert response_data["device_type"] == str(new_dt.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
            assert asp.content_s == old_content
            assert asp.device_type == old_dt
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asp.content_s == old_content
        assert asp.device_type == old_dt


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_with_missing_content(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request allows creating
    an AdditionalSignPlan without content_s when missing_content is set.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "missing_content": True,
    }

    assert AdditionalSignPlan.objects.count() == 0

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED, response_data
        assert AdditionalSignPlan.objects.count() == 1
        asp = AdditionalSignPlan.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["device_type"] == str(data["device_type"])
        assert response_data["content_s"] is None
        assert response_data["missing_content"] is True
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignPlan.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_plan__create_dont_accept_content_when_missing_content_is_enabled(admin_user):
    """
    Test that AdditionalSignPlan API endpoint POST request doesn't accept content when missing_content is enabled.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_plan()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content_valid_by_simple_schema,
        "missing_content": True,
    }

    assert AdditionalSignPlan.objects.count() == 0

    response = client.post(reverse("v1:additionalsignplan-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response_data["missing_content"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignPlan.objects.count() == 0


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
def test__additional_sign_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    asp = get_additional_sign_plan(owner=get_owner(name_en="Old owner", name_fi="Vanha omistaja"))
    kwargs = {"pk": asp.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:additionalsignplan-{view_type}", kwargs=kwargs)
    data = {"owner": str(get_owner(name_en="New owner", name_fi="Uusi omistaja").pk)}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert AdditionalSignPlan.objects.count() == 1
    assert AdditionalSignPlan.objects.first().is_active
    assert AdditionalSignPlan.objects.first().owner.name_en == "Old owner"
    assert response.status_code == expected_status
