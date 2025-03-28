import datetime
import json

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.models.furniture_signpost import ArrowDirection
from city_furniture.tests.factories import (
    add_furniture_signpost_real_operation,
    DEFAULT_DEVICE_TYPE_DESCRIPTION,
    FurnitureSignpostPlanFactory,
    FurnitureSignpostRealFactory,
    get_city_furniture_device_type,
    get_furniture_signpost_plan,
    get_furniture_signpost_real,
)
from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.models import GroupResponsibleEntity
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    get_api_client,
    get_operation_type,
    get_owner,
    get_responsible_entity_project,
    get_user,
    OwnerFactory,
    PlanFactory,
)
from traffic_control.tests.test_base_api import illegal_test_point
from traffic_control.tests.test_base_api_3d import test_point_2_3d, test_point_3d
from traffic_control.tests.utils import MIN_X, MIN_Y

TEST_POINT1_EWKT = f"SRID=3879;POINT Z ({MIN_X + 1} {MIN_Y + 1} 0)"
TEST_POINT2_EWKT = f"SRID=3879;POINT Z ({MIN_X + 2} {MIN_Y + 2} 0)"


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
        assert result["device_type_description"] == DEFAULT_DEVICE_TYPE_DESCRIPTION
        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("arrow_direction", ArrowDirection.RIGHT, ArrowDirection.TOP_RIGHT),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
    ),
)
@pytest.mark.django_db
def test__furniture_signpost_plans_filtering__list(field_name, value, second_value):
    do_filtering_test(
        FurnitureSignpostPlanFactory,
        "v1:furnituresignpostplan-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.parametrize("plan_decision_id", (None, "TEST-DECISION-ID"))
@pytest.mark.django_db
def test__furniture_signpost_real__list(geo_format, plan_decision_id):
    client = get_api_client()
    plan = PlanFactory(decision_id=plan_decision_id) if plan_decision_id else None

    for owner_name in ["foo", "bar", "baz"]:
        fsp = FurnitureSignpostPlanFactory(plan=plan, parent=None)
        get_furniture_signpost_real(owner=get_owner(name_fi=owner_name), furniture_signpost_plan=fsp)

    response = client.get(reverse("v1:furnituresignpostreal-list"), data={"geo_format": geo_format})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["count"] == 3
    for result in response_data["results"]:
        obj = FurnitureSignpostReal.objects.get(pk=result["id"])
        assert result["device_type_description"] == DEFAULT_DEVICE_TYPE_DESCRIPTION
        assert result["plan_decision_id"] == plan_decision_id
        if geo_format == "geojson":
            assert result["location"] == GeoJsonDict(obj.location.json)
        else:
            assert result["location"] == obj.location.ewkt


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("arrow_direction", ArrowDirection.RIGHT, ArrowDirection.TOP_RIGHT),
        ("condition", Condition.GOOD, Condition.VERY_GOOD),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.OTHER),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
    ),
)
@pytest.mark.django_db
def test__furniture_signpost_reals_filtering__list(field_name, value, second_value):
    do_filtering_test(
        FurnitureSignpostRealFactory,
        "v1:furnituresignpostreal-list",
        field_name,
        value,
        second_value,
    )


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
    assert response_data["device_type_description"] == DEFAULT_DEVICE_TYPE_DESCRIPTION
    if geo_format == "geojson":
        assert response_data["location"] == GeoJsonDict(obj.location.json)
    else:
        assert response_data["location"] == obj.location.ewkt


@pytest.mark.django_db
@pytest.mark.parametrize("geo_format", ("", "geojson"))
@pytest.mark.parametrize("plan_decision_id", (None, "TEST-DECISION-ID"))
def test__furniture_signpost_real__detail(geo_format, plan_decision_id):
    client = get_api_client()
    plan = PlanFactory(decision_id=plan_decision_id) if plan_decision_id else None
    fsp = get_furniture_signpost_plan(plan=plan)
    obj = get_furniture_signpost_real(furniture_signpost_plan=fsp)
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
    assert response_data["device_type_description"] == DEFAULT_DEVICE_TYPE_DESCRIPTION
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]
    assert response_data["plan_decision_id"] == plan_decision_id
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
def test__furniture_signpost_real__create_with_existing_plan(admin_user):
    """
    Test that FurnitureSignpostReal API does not create a new db row when
    signpost with the same plan already exists
    """
    client = get_api_client(user=get_user(admin=admin_user))
    fsp_plan = FurnitureSignpostPlanFactory(parent=None)
    existing_fsp = get_furniture_signpost_real(furniture_signpost_plan=fsp_plan)
    data = {
        "location": str(existing_fsp.location),
        "owner": get_owner().pk,
        "furniture_signpost_plan": fsp_plan.pk,
        "device_type": fsp_plan.device_type.pk,
    }

    response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
    response_data = response.json()
    # just the parent_ads should be in the database
    assert FurnitureSignpostReal.objects.count() == 1
    if admin_user:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "duplicate key value violates unique constraint" in response_data["detail"]
        assert "city_furniture_furnituresignpostreal_unique_furniture_signpost" in response_data["detail"]
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN


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


@pytest.mark.django_db
def test__furniture_signpost_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "device_type": get_city_furniture_device_type().pk,
    }
    do_illegal_geometry_test(
        "v1:furnituresignpostplan-list",
        data,
        [f"Geometry for furnituresignpostplan {illegal_test_point.ewkt} is not legal"],
    )


@pytest.mark.django_db
def test__furniture_signpost_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "device_type": get_city_furniture_device_type().pk,
    }
    do_illegal_geometry_test(
        "v1:furnituresignpostreal-list",
        data,
        [f"Geometry for furnituresignpostreal {illegal_test_point.ewkt} is not legal"],
    )


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


# Responsible Entity permissions
@pytest.mark.parametrize("add_to_responsible_entity", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__responsible_entity_permission__create(add_to_responsible_entity):
    user = get_user(admin=False, bypass_operational_area=True)
    user.user_permissions.add(Permission.objects.get(codename="add_furnituresignpostreal"))
    client = get_api_client(user=user)
    responsible_entity = get_responsible_entity_project()
    data = {
        "location": str(test_point_3d),
        "owner": get_owner().pk,
        "device_type": get_city_furniture_device_type().pk,
        "responsible_entity": responsible_entity.pk,
    }

    if add_to_responsible_entity:
        user.responsible_entities.add(responsible_entity)
        response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert FurnitureSignpostReal.objects.count() == 1
    else:
        response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FurnitureSignpostReal.objects.count() == 0


@pytest.mark.parametrize("add_to_responsible_entity", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__responsible_entity_permission__delete(add_to_responsible_entity):
    user = get_user(admin=False, bypass_operational_area=True)
    user.user_permissions.add(Permission.objects.get(codename="delete_furnituresignpostreal"))
    client = get_api_client(user=user)
    responsible_entity = get_responsible_entity_project()
    instance = get_furniture_signpost_real(responsible_entity=responsible_entity)

    if add_to_responsible_entity:
        user.responsible_entities.add(instance.responsible_entity)
        response = client.delete(reverse("v1:furnituresignpostreal-detail", kwargs={"pk": instance.pk}))
        instance.refresh_from_db()
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not instance.is_active
    else:
        response = client.delete(reverse("v1:furnituresignpostreal-detail", kwargs={"pk": instance.pk}))
        instance.refresh_from_db()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert instance.is_active


@pytest.mark.parametrize("add_to_responsible_entity", (False, True))
@pytest.mark.django_db
def test__furniture_signpost_real__create__responsible_entity_permission__group(add_to_responsible_entity):
    user = get_user(admin=False, bypass_operational_area=True)
    user.user_permissions.add(Permission.objects.get(codename="add_furnituresignpostreal"))
    group = Group.objects.create(name="test group")
    user.groups.add(group)
    client = get_api_client(user=user)
    responsible_entity = get_responsible_entity_project()
    data = {
        "location": str(test_point_3d),
        "owner": get_owner().pk,
        "device_type": get_city_furniture_device_type().pk,
        "responsible_entity": responsible_entity.pk,
    }

    if add_to_responsible_entity:
        gre = GroupResponsibleEntity.objects.create(group=group)
        gre.responsible_entities.add(responsible_entity)
        response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert FurnitureSignpostReal.objects.count() == 1
    else:
        response = client.post(reverse("v1:furnituresignpostreal-list"), data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert FurnitureSignpostReal.objects.count() == 0


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
def test__furniture_signpost_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_furniture_signpost_plan(location=TEST_POINT1_EWKT)
    kwargs = {"pk": signpost.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:furnituresignpostplan-{view_type}", kwargs=kwargs)
    data = {
        "location": TEST_POINT2_EWKT,
        "device_type": str(get_city_furniture_device_type().id),
        "owner": str(get_owner().id),
    }
    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert FurnitureSignpostPlan.objects.count() == 1
    assert FurnitureSignpostPlan.objects.first().is_active
    assert FurnitureSignpostPlan.objects.first().location == TEST_POINT1_EWKT
    assert response.status_code == expected_status


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
def test__furniture_signpost_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_furniture_signpost_real(location=TEST_POINT1_EWKT)
    kwargs = {"pk": signpost.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:furnituresignpostreal-{view_type}", kwargs=kwargs)
    data = {
        "location": TEST_POINT2_EWKT,
        "device_type": str(get_city_furniture_device_type().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert FurnitureSignpostReal.objects.count() == 1
    assert FurnitureSignpostReal.objects.first().is_active
    assert FurnitureSignpostReal.objects.first().location == TEST_POINT1_EWKT
    assert response.status_code == expected_status


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
def test__furniture_signpost_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    signpost = get_furniture_signpost_real()
    operation_type = get_operation_type()
    operation = add_furniture_signpost_real_operation(
        furniture_signpost_real=signpost,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"furniture_signpost_real_pk": signpost.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"furniture-signpost-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert signpost.operations.all().count() == 1
    assert signpost.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
