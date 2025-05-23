import datetime
import json

import pytest
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import (
    Condition,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    Reflection,
    Size,
    Surface,
)
from traffic_control.models import AdditionalSignReal
from traffic_control.models.additional_sign import Color, LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_additional_sign_real_operation,
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    get_api_client,
    get_operation_type,
    get_owner,
    get_traffic_control_device_type,
    get_traffic_sign_real,
    get_user,
    PlanFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignRealFactory,
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
from traffic_control.tests.test_base_api import illegal_test_point

# AdditionalSignReal tests
# ===============================================


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.parametrize("plan_decision_id", (None, "TEST-DECISION-ID"))
@pytest.mark.django_db
def test__additional_sign_real__list(geo_format, plan_decision_id):
    client = get_api_client()
    plan = PlanFactory(decision_id=plan_decision_id) if plan_decision_id else None

    for owner_name in ["foo", "bar", "baz"]:
        ads_plan = AdditionalSignPlanFactory(plan=plan) if plan else None
        AdditionalSignRealFactory(owner=get_owner(name_fi=owner_name), additional_sign_plan=ads_plan)

    response = client.get(reverse("v1:additionalsignreal-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = AdditionalSignReal.objects.get(pk=result["id"])

        assert result["plan_decision_id"] == plan_decision_id
        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("color", Color.BLUE, Color.YELLOW),
        ("condition", Condition.GOOD, Condition.VERY_GOOD),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.OTHER),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.BIKE, LaneType.HEAVY),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.ABOVE, LocationSpecifier.MIDDLE),
        ("reflection_class", Reflection.R1, Reflection.R2),
        ("size", Size.LARGE, Size.MEDIUM),
        ("surface_class", Surface.FLAT, Surface.CONVEX),
    ),
)
@pytest.mark.django_db
def test__additional_sign_real_filtering__list(field_name, value, second_value):
    do_filtering_test(
        AdditionalSignRealFactory,
        "v1:additionalsignreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.parametrize("plan_decision_id", (None, "TEST-DECISION-ID"))
@pytest.mark.django_db
def test__additional_sign_real__detail(geo_format, plan_decision_id):
    client = get_api_client()
    plan = PlanFactory(decision_id=plan_decision_id) if plan_decision_id else None
    ads_plan = AdditionalSignPlanFactory(plan=plan) if plan else None
    asr = AdditionalSignRealFactory(parent=get_traffic_sign_real(), additional_sign_plan=ads_plan)
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
    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response_data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]
    assert response_data["plan_decision_id"] == plan_decision_id

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
        asr = AdditionalSignReal.objects.first()
        assert response_data["id"] == str(asr.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_existing_plan(admin_user):
    """
    Test that AdditionalSignReal API does not create a new db row when
    additional sign with the same plan already exists
    """
    client = get_api_client(user=get_user(admin=admin_user))
    ads_plan = AdditionalSignPlanFactory()
    existing_ads = AdditionalSignRealFactory(additional_sign_plan=ads_plan)
    data = {
        "location": str(existing_ads.location),
        "owner": str(get_owner().pk),
        "additional_sign_plan": str(ads_plan.pk),
        "parent": TrafficSignRealFactory().pk,
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()
    # just the parent_ads should be in the database
    assert AdditionalSignReal.objects.count() == 1
    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "duplicate key value violates unique constraint" in response_data["detail"]
        assert "traffic_control_additionalsignreal_unique_additional_sign_plan" in response_data["detail"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request creates
    an AdditionalSignReal with content_s.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_real()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content_valid_by_simple_schema,
    }

    assert AdditionalSignReal.objects.count() == 0

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED
        assert AdditionalSignReal.objects.count() == 1
        asr = AdditionalSignReal.objects.first()
        assert response_data["id"] == str(asr.pk)
        assert response_data["parent"] == str(data["parent"])
        assert response_data["owner"] == str(data["owner"])
        assert response_data["device_type"] == str(data["device_type"])
        assert response_data["content_s"] == data["content_s"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignReal.objects.count() == 0


@pytest.mark.parametrize(
    "schema,content",
    (
        (None, simple_schema),
        (simple_schema, content_invalid_by_simple_schema),
    ),
)
@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_content_invalid(schema, content, admin_user):
    """
    Test that AdditionalSignReal API endpoint POST doesn't create
    an AdditionalSignReal when content_s is invalid to device type's content_schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_real()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content,
    }

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response_data["content_s"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignReal.objects.count() == 0


@pytest.mark.django_db
def test__additional_sign_real__create_with_invalid_geometry():
    data = {"location": illegal_test_point.ewkt, "owner": str(get_owner().pk), "parent": TrafficSignRealFactory().pk}
    do_illegal_geometry_test(
        "v1:additionalsignreal-list",
        data,
        [f"Geometry for additionalsignreal {illegal_test_point.ewkt} is not legal"],
    )


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
def test__additional_sign_real__update_device_type_and_content(
    old_schema,
    old_content,
    new_schema,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignReal API endpoint PUT request update
    is successful when changing both device_type and content_s, but is
    not successful when structured content doesn't match device type's content_schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    old_dt = get_traffic_control_device_type(code="A1234", content_schema=old_schema)
    new_dt = get_traffic_control_device_type(code="new_code", content_schema=new_schema)
    asr = AdditionalSignRealFactory(content_s=old_content, device_type=old_dt, missing_content=False)

    data = {
        "parent": asr.parent.pk,
        "location": str(asr.parent.location),
        "owner": get_owner(name_en="New owner").pk,
        "device_type": new_dt.id,
        "content_s": new_content,
    }

    response = client.put(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == str(asr.pk)
            assert response_data["owner"] == str(data["owner"])
            assert response_data["device_type"] == str(data["device_type"])
            assert response_data["content_s"] == data["content_s"]
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner.pk != data["owner"]
        assert asr.device_type != data["device_type"]

        if old_content == new_content:
            assert asr.content_s == data["content_s"]
        else:
            assert asr.content_s != data["content_s"]


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__partial_update_without_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint PATCH request update
    is successful when content is not defined.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = TrafficControlDeviceTypeFactory(code="A1234")
    traffic_sign_real = TrafficSignRealFactory(device_type=dt)
    asr = AdditionalSignRealFactory(missing_content=False, parent=traffic_sign_real)

    data = {
        "parent": traffic_sign_real.pk,
        "location": str(traffic_sign_real.location),
        "owner": get_owner(name_en="New owner").pk,
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    if admin_user:
        assert response.status_code == status.HTTP_200_OK
        assert response_data["id"] == str(asr.pk)
        assert response_data["owner"] == str(data["owner"])
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.owner != data["owner"]


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
def test__additional_sign_real__partial_update_content(
    schema,
    old_content,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignReal API endpoint PATCH request updates
    structured content when it's valid according to device type's content schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    dt = TrafficControlDeviceTypeFactory(code="DT1", content_schema=schema)
    asr = AdditionalSignRealFactory(device_type=dt, content_s=old_content, missing_content=False)
    asr_id = str(asr.pk)
    data = {
        "content_s": new_content,
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr_id}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == asr_id
            assert response_data["content_s"] == new_content
            assert response_data["device_type"] == str(dt.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
            assert asr.content_s == old_content
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.content_s == old_content


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
def test__additional_sign_real__partial_update_device_type_and_content(
    old_schema,
    new_schema,
    old_content,
    new_content,
    expect_valid,
    admin_user,
):
    """
    Test that AdditionalSignReal API endpoint PATCH request updates structured
    content and device type when content is valid according to device type's content schema.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    old_dt = TrafficControlDeviceTypeFactory(code="DT1", content_schema=old_schema)
    new_dt = TrafficControlDeviceTypeFactory(code="DT2", content_schema=new_schema)
    asr = AdditionalSignRealFactory(device_type=old_dt, content_s=old_content, missing_content=False)
    asr_id = str(asr.pk)
    data = {
        "content_s": new_content,
        "device_type": str(new_dt.id),
    }

    response = client.patch(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr_id}), data=data)
    response_data = response.json()
    asr.refresh_from_db()

    if admin_user:
        if expect_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data["id"] == asr_id
            assert response_data["content_s"] == new_content
            assert response_data["device_type"] == str(new_dt.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert len(response_data["content_s"]) == 1
            assert asr.content_s == old_content
            assert asr.device_type == old_dt
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert asr.content_s == old_content
        assert asr.device_type == old_dt


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_with_missing_content(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request allows creating
    an AdditionalSignReal without content_s when missing_content is set.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_real()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "missing_content": True,
    }

    assert AdditionalSignReal.objects.count() == 0

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_201_CREATED, response_data
        assert AdditionalSignReal.objects.count() == 1
        asp = AdditionalSignReal.objects.first()
        assert response_data["id"] == str(asp.pk)
        assert response_data["device_type"] == str(data["device_type"])
        assert response_data["content_s"] is None
        assert response_data["missing_content"] is True
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert AdditionalSignReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__create_dont_accept_content_when_missing_content_is_enabled(admin_user):
    """
    Test that AdditionalSignReal API endpoint POST request doesn't accept content when missing_content is enabled.
    """
    client = get_api_client(user=get_user(admin=admin_user))
    tsp = get_traffic_sign_real()
    dt = get_traffic_control_device_type(code=get_random_string(length=12), content_schema=simple_schema)

    data = {
        "parent": str(tsp.pk),
        "location": str(tsp.location),
        "owner": str(get_owner().pk),
        "device_type": str(dt.pk),
        "content_s": content_valid_by_simple_schema,
        "missing_content": True,
    }

    assert AdditionalSignReal.objects.count() == 0

    response = client.post(reverse("v1:additionalsignreal-list"), data=data)
    response_data = response.json()

    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert len(response_data["missing_content"]) == 1
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN

    assert AdditionalSignReal.objects.count() == 0


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real__delete(admin_user):
    user = get_user(admin=admin_user)
    client = get_api_client(user=user)
    asr = AdditionalSignRealFactory()

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
    asr = AdditionalSignRealFactory()
    asr.soft_delete(user)

    response = client.get(reverse("v1:additionalsignreal-detail", kwargs={"pk": asr.pk}))

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
def test__additional_sign_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    asr = AdditionalSignRealFactory(owner=get_owner(name_en="Old owner", name_fi="Vanha omistaja"))
    kwargs = {"pk": asr.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:additionalsignreal-{view_type}", kwargs=kwargs)
    data = {"owner": str(get_owner(name_en="New owner", name_fi="Uusi omistaja").pk)}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert AdditionalSignReal.objects.count() == 1
    assert AdditionalSignReal.objects.first().is_active
    assert AdditionalSignReal.objects.first().owner.name_en == "Old owner"
    assert response.status_code == expected_status


# AdditionalSignRealOperation tests
# ===============================================


@pytest.mark.parametrize("admin_user", (False, True))
@pytest.mark.django_db
def test__additional_sign_real_operation__create(admin_user):
    client = get_api_client(user=get_user(admin=admin_user))
    asr = AdditionalSignRealFactory()
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
    asr = AdditionalSignRealFactory()
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
def test__additional_sign_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    asr = AdditionalSignRealFactory()
    operation_type = get_operation_type()
    operation = add_additional_sign_real_operation(
        additional_sign_real=asr,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"additional_sign_real_pk": asr.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"additional-sign-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert asr.operations.all().count() == 1
    assert asr.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
