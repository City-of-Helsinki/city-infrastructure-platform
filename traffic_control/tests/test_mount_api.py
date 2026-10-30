import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import Condition, InstallationStatus, Lifecycle
from traffic_control.models import MountPlan, MountReal, MountType
from traffic_control.models.mount import LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_mount_real_operation,
    get_api_client,
    get_mount_plan,
    get_mount_real,
    get_operation_type,
    MountPlanFactory,
    MountRealFactory,
    OwnerFactory,
    PlanFactory,
)
from traffic_control.tests.test_base_api import (
    illegal_test_point,
    line_location_error_test_data,
    line_location_test_data,
    point_location_error_test_data,
    point_location_test_data,
    test_point,
)
from traffic_control.tests.utils import MIN_X, MIN_Y

# ==============================================================================
# Fixtures for API tests
# ==============================================================================


@pytest.fixture
def test_mount_type():
    return MountType.objects.create(code="PORTAL", description="Portal")


@pytest.fixture
def test_mount_type_2():
    return MountType.objects.create(code="WALL", description="Wall")


@pytest.fixture
def create_mount_plan(admin_user, test_mount_type, test_owner):
    def _create(**overrides):
        defaults = {
            "mount_type": test_mount_type,
            "location": test_point,
            "lifecycle": Lifecycle.ACTIVE,
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return MountPlan.objects.create(**defaults)

    return _create


@pytest.fixture
def create_mount_real(admin_user, test_mount_type, test_owner, create_mount_plan):
    def _create(mount_plan=None, **overrides):
        if mount_plan is None:
            mount_plan = create_mount_plan()

        defaults = {
            "mount_plan": mount_plan,
            "mount_type": test_mount_type,
            "location": test_point,
            "installation_date": datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            "lifecycle": Lifecycle.ACTIVE,
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return MountReal.objects.create(**defaults)

    return _create


# ==============================================================================
# MountPlan Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_mount_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    mount_plan = get_mount_plan(location)
    response = api_client.get(reverse("v1:mountplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(mount_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_mount_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_mount_plan(location)
    response = api_client.get(reverse("v1:mountplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.django_db
def test__mount_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:mountplan-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_mount_plans(admin_api_client, create_mount_plan):
    """
    Ensure we can get all mount plan objects.
    """
    count = 3
    for _ in range(count):
        create_mount_plan()
    response = admin_api_client.get(reverse("v1:mountplan-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        mount_plan = MountPlan.objects.get(id=result.get("id"))
        assert result.get("location") == mount_plan.location.ewkt


@pytest.mark.django_db
def test_get_all_mount_plans__geojson(admin_api_client, create_mount_plan):
    """
    Ensure we can get all mount plan objects with GeoJSON location.
    """
    count = 3
    for _ in range(count):
        create_mount_plan()
    response = admin_api_client.get(reverse("v1:mountplan-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        mount_plan = MountPlan.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(mount_plan.location.json)


@pytest.mark.django_db
def test_get_mount_plan_detail(admin_api_client, create_mount_plan):
    """
    Ensure we can get one mount plan object.
    """
    mount_plan = create_mount_plan()
    response = admin_api_client.get(reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(mount_plan.id)
    assert mount_plan.location.ewkt == response.data.get("location")


@pytest.mark.django_db
def test_get_mount_plan_detail__geojson(admin_api_client, create_mount_plan):
    """
    Ensure we can get one mount plan object with GeoJSON location.
    """
    mount_plan = create_mount_plan()
    response = admin_api_client.get(
        reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(mount_plan.id)
    mount_plan_geojson = GeoJsonDict(mount_plan.location.json)
    assert mount_plan_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_mount_plan(admin_api_client, test_mount_type, test_owner):
    """
    Ensure we can create a new mount plan object.
    """
    data = {
        "mount_type": test_mount_type.pk,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
    }
    response = admin_api_client.post(reverse("v1:mountplan-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert MountPlan.objects.count() == 1
    assert response.data.get("location") == data["location"]
    mount_plan = MountPlan.objects.first()
    assert mount_plan.mount_type.pk == data["mount_type"]
    assert mount_plan.location.ewkt == data["location"]
    assert mount_plan.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_update_mount_plan(admin_api_client, test_mount_type_2, test_owner, create_mount_plan):
    """
    Ensure we can update existing mount plan object.
    """
    mount_plan = create_mount_plan()
    data = {
        "mount_type": test_mount_type_2.pk,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
    }
    response = admin_api_client.put(
        reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert MountPlan.objects.count() == 1
    mount_plan = MountPlan.objects.first()
    assert mount_plan.mount_type.pk == data["mount_type"]
    assert mount_plan.location.ewkt == data["location"]
    assert mount_plan.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_mount_plan_detail(admin_api_client, admin_user, create_mount_plan):
    """
    Ensure we can soft-delete one mount plan object.
    """
    mount_plan = create_mount_plan()
    response = admin_api_client.delete(
        reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert MountPlan.objects.count() == 1
    deleted_mount_plan = MountPlan.objects.get(id=str(mount_plan.id))
    assert deleted_mount_plan.id == mount_plan.id
    assert not deleted_mount_plan.is_active
    assert deleted_mount_plan.deleted_by == admin_user
    assert deleted_mount_plan.deleted_at


@pytest.mark.django_db
def test_get_deleted_mount_plan_returns_not_found(admin_api_client, create_mount_plan):
    mount_plan = create_mount_plan()
    response = admin_api_client.delete(
        reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:mountplan-detail", kwargs={"pk": mount_plan.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.RIGHT, LocationSpecifier.MIDDLE),
    ),
)
@pytest.mark.django_db
def test__mount_plan_filtering__list(field_name, value, second_value):
    do_filtering_test(
        MountPlanFactory,
        "v1:mountplan-list",
        field_name,
        value,
        second_value,
    )


# ==============================================================================
# MountReal Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_mount_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    mount_real = get_mount_real(location)
    response = api_client.get(reverse("v1:mountreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(mount_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_mount_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_mount_real(location)
    response = api_client.get(reverse("v1:mountreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("condition", Condition.VERY_GOOD, Condition.AVERAGE),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.COVERED),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.RIGHT, LocationSpecifier.MIDDLE),
    ),
)
@pytest.mark.django_db
def test__mount_real_filtering__list(field_name, value, second_value):
    do_filtering_test(
        MountRealFactory,
        "v1:mountreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
def test__mount_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:mountreal-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_mount_reals(admin_api_client, create_mount_real):
    """
    Ensure we can get all mount real objects.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

    count = 3
    for _ in range(count):
        mp = MountPlanFactory(plan=plan)
        create_mount_real(mount_plan=mp)
    response = admin_api_client.get(reverse("v1:mountreal-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        mount_real = MountReal.objects.get(id=result.get("id"))
        assert result.get("location") == mount_real.location.ewkt
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_all_mount_reals__geojson(admin_api_client, create_mount_real):
    """
    Ensure we can get all mount real objects with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

    count = 3
    for _ in range(count):
        mp = MountPlanFactory(plan=plan)
        create_mount_real(mount_plan=mp)
    response = admin_api_client.get(reverse("v1:mountreal-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        mount_real = MountReal.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(mount_real.location.json)
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_mount_real_detail(admin_api_client, create_mount_real):
    """
    Ensure we can get one mount real object.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    mp = get_mount_plan(plan=plan)

    mount_real = create_mount_real(mount_plan=mp)
    operation_1 = add_mount_real_operation(mount_real, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_mount_real_operation(mount_real, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_mount_real_operation(mount_real, operation_date=datetime.date(2020, 11, 10))
    response = admin_api_client.get(reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(mount_real.id)
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"
    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response.data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]


@pytest.mark.django_db
def test_get_mount_real_detail__geojson(admin_api_client, create_mount_real):
    """
    Ensure we can get one mount real object.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    mp = get_mount_plan(plan=plan)

    mount_real = create_mount_real(mount_plan=mp)
    response = admin_api_client.get(
        reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(mount_real.id)
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"
    mount_real_geojson = GeoJsonDict(mount_real.location.json)
    assert mount_real_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_mount_real(admin_api_client, test_mount_type, test_owner):
    """
    Ensure we can create a new mount real object.
    """
    data = {
        "mount_type": test_mount_type.pk,
        "location": test_point.ewkt,
        "installation_date": "2020-01-02",
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
    }
    response = admin_api_client.post(reverse("v1:mountreal-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert MountReal.objects.count() == 1
    assert response.data.get("location") == data["location"]
    mount_real = MountReal.objects.first()
    assert mount_real.mount_type.pk == data["mount_type"]
    assert mount_real.location.ewkt == data["location"]
    assert mount_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert mount_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_create_mount_real_with_existing_plan(admin_api_client, test_mount_type, test_owner):
    mount_plan = MountPlanFactory()
    MountRealFactory(mount_plan=mount_plan)
    data = {
        "mount_type": test_mount_type.pk,
        "location": test_point.ewkt,
        "installation_date": "2020-01-02",
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "mount_plan": mount_plan.pk,
    }
    response = admin_api_client.post(reverse("v1:mountreal-list"), data, format="json")
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert MountReal.objects.count() == 1
    assert "duplicate key value violates unique constraint" in response_data["detail"]
    assert "traffic_control_mountreal_unique_mount_plan" in response_data["detail"]


@pytest.mark.django_db
def test_update_mount_real(admin_api_client, test_mount_type_2, test_owner, create_mount_real):
    """
    Ensure we can update existing mount real object.
    """
    mount_real = create_mount_real()
    data = {
        "mount_type": test_mount_type_2.pk,
        "location": test_point.ewkt,
        "installation_date": "2020-01-03",
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
    }
    response = admin_api_client.put(
        reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert MountReal.objects.count() == 1
    mount_real = MountReal.objects.first()
    assert mount_real.mount_type.pk == data["mount_type"]
    assert mount_real.location.ewkt == data["location"]
    assert mount_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert mount_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_mount_real_detail(admin_api_client, admin_user, create_mount_real):
    """
    Ensure we can soft-delete one mount real object.
    """
    mount_real = create_mount_real()
    response = admin_api_client.delete(
        reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert MountReal.objects.count() == 1
    deleted_mount_real = MountReal.objects.get(id=str(mount_real.id))
    assert deleted_mount_real.id == mount_real.id
    assert not deleted_mount_real.is_active
    assert deleted_mount_real.deleted_by == admin_user
    assert deleted_mount_real.deleted_at


@pytest.mark.django_db
def test_get_deleted_mount_real_returns_not_found(admin_api_client, create_mount_real):
    mount_real = create_mount_real()
    response = admin_api_client.delete(
        reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:mountreal-detail", kwargs={"pk": mount_real.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_operation_mount_real(admin_api_client, create_mount_real):
    mount_real = create_mount_real()
    operation_type = get_operation_type()
    data = {
        "operation_date": "2020-01-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse("mount-real-operations-list", kwargs={"mount_real_pk": mount_real.pk})
    response = admin_api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert mount_real.operations.all().count() == 1


@pytest.mark.django_db
def test_update_operation_mount_real(admin_api_client, create_mount_real):
    mount_real = create_mount_real()
    operation_type = get_operation_type()
    operation = add_mount_real_operation(
        mount_real=mount_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {
        "operation_date": "2020-02-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse(
        "mount-real-operations-detail",
        kwargs={"mount_real_pk": mount_real.pk, "pk": operation.pk},
    )
    response = admin_api_client.put(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert mount_real.operations.all().count() == 1
    assert mount_real.operations.all().first().operation_date == datetime.date(2020, 2, 1)


# ==============================================================================
# Anonymous User Tests
# ==============================================================================


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
def test__mount_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    mount = get_mount_plan(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": mount.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:mountplan-{view_type}", kwargs=kwargs)
    data = {"location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert MountPlan.objects.count() == 1
    assert MountPlan.objects.first().is_active
    assert MountPlan.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__mount_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    mount = get_mount_real(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": mount.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:mountreal-{view_type}", kwargs=kwargs)
    data = {"location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert MountReal.objects.count() == 1
    assert MountReal.objects.first().is_active
    assert MountReal.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__mount_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    mount = get_mount_real()
    operation_type = get_operation_type()
    operation = add_mount_real_operation(
        mount_real=mount,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"mount_real_pk": mount.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"mount-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert mount.operations.all().count() == 1
    assert mount.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
