import datetime
import json

import pytest
from auditlog.models import LogEntry
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import Condition, DeviceTypeTargetModel, InstallationStatus, LaneNumber, LaneType, Lifecycle
from traffic_control.models import BarrierPlan, BarrierReal, ConnectionType, Reflective
from traffic_control.models.barrier import LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_barrier_real_operation,
    BarrierPlanFactory,
    BarrierRealFactory,
    get_api_client,
    get_barrier_plan,
    get_operation_type,
    get_user,
    OwnerFactory,
    PlanFactory,
    TrafficControlDeviceTypeFactory,
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
def create_barrier_plan(admin_user, test_device_type, test_owner):
    def _create(**overrides):
        defaults = {
            "device_type": test_device_type,
            "location": test_point,
            "lifecycle": Lifecycle.ACTIVE,
            "material": "Betoni",
            "reflective": Reflective.YES,
            "connection_type": ConnectionType.OPEN_OUT,
            "road_name": "Testingroad",
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return BarrierPlan.objects.create(**defaults)

    return _create


@pytest.fixture
def create_barrier_real(admin_user, test_device_type, test_owner, create_barrier_plan):
    def _create(barrier_plan=None, **overrides):
        if barrier_plan is None:
            barrier_plan = create_barrier_plan()

        defaults = {
            "device_type": test_device_type,
            "barrier_plan": barrier_plan,
            "location": test_point,
            "installation_date": datetime.datetime.strptime("20012020", "%d%m%Y").date(),
            "lifecycle": Lifecycle.ACTIVE,
            "material": "Betoni",
            "reflective": Reflective.YES,
            "connection_type": ConnectionType.OPEN_OUT,
            "road_name": "Testingroad",
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return BarrierReal.objects.create(**defaults)

    return _create


# ==============================================================================
# BarrierPlan Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_barrier_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    barrier_plan = BarrierPlanFactory(location=location)
    response = api_client.get(reverse("v1:barrierplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected
    if expected == 1:
        data = response.data.get("results")[0]
        assert str(barrier_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_barrier_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    BarrierPlanFactory(location=location)
    response = api_client.get(reverse("v1:barrierplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("connection_type", ConnectionType.OPEN_OUT, ConnectionType.CLOSED),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.BIKE, LaneType.HEAVY),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.RIGHT, LocationSpecifier.MIDDLE),
        ("reflective", Reflective.YES, Reflective.RED_YELLOW),
    ),
)
@pytest.mark.django_db
def test__barrier_plan_filtering__list(field_name, value, second_value):
    do_filtering_test(
        BarrierPlanFactory,
        "v1:barrierplan-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.BARRIER))
def test__barrier_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    barrier_plan = BarrierPlanFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.pk}),
        data,
        format="json",
    )

    barrier_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert barrier_plan.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__barrier_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    barrier_plan = BarrierPlanFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.pk}),
        data,
        format="json",
    )

    barrier_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert barrier_plan.device_type != device_type


@pytest.mark.django_db
def test__barrier_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "road_name": "TestRoad",
        "device_type": TrafficControlDeviceTypeFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:barrierplan-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_barrier_plans(admin_api_client, create_barrier_plan):
    """
    Ensure we can get all barrier plan objects.
    """
    count = 3
    for _ in range(count):
        create_barrier_plan()

    response = admin_api_client.get(reverse("v1:barrierplan-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        barrier_plan = BarrierPlan.objects.get(id=result.get("id"))
        assert result.get("location") == barrier_plan.location.ewkt


@pytest.mark.django_db
def test_get_all_barrier_plans__geojson(admin_api_client, create_barrier_plan):
    """
    Ensure we can get all barrier plan objects with GeoJSON location.
    """
    count = 3
    for _ in range(count):
        create_barrier_plan()

    response = admin_api_client.get(reverse("v1:barrierplan-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        barrier_plan = BarrierPlan.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(barrier_plan.location.json)


@pytest.mark.django_db
def test_get_barrier_plan_detail(admin_api_client, create_barrier_plan):
    """
    Ensure we can get one barrier plan object.
    """
    barrier_plan = create_barrier_plan()
    response = admin_api_client.get(reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(barrier_plan.id)
    assert barrier_plan.location.ewkt == response.data.get("location")


@pytest.mark.django_db
def test_get_barrier_plan_detail__geojson(admin_api_client, create_barrier_plan):
    """
    Ensure we can get one barrier plan object with GeoJSON location.
    """
    barrier_plan = create_barrier_plan()
    response = admin_api_client.get(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
        data={"geo_format": "geojson"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(barrier_plan.id)
    barrier_plan_geojson = GeoJsonDict(barrier_plan.location.json)
    assert barrier_plan_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_barrier_plan(admin_api_client, test_device_type, test_owner):
    """
    Ensure we can create a new barrier plan object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "road_name": "Test street 1",
    }
    response = admin_api_client.post(reverse("v1:barrierplan-list"), data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert BarrierPlan.objects.count() == 1
    assert response.data.get("location") == data["location"]

    barrier_plan = BarrierPlan.objects.first()
    assert barrier_plan.device_type.id == data["device_type"]
    assert barrier_plan.location.ewkt == data["location"]
    assert barrier_plan.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_update_barrier_plan(admin_api_client, test_device_type, test_owner, create_barrier_plan):
    """
    Ensure we can update existing barrier plan object.
    """
    barrier_plan = create_barrier_plan()
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "road_name": "Test street 1",
    }
    response = admin_api_client.put(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
        data,
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert BarrierPlan.objects.count() == 1

    barrier_plan = BarrierPlan.objects.first()
    assert barrier_plan.device_type.id == data["device_type"]
    assert barrier_plan.location.ewkt == data["location"]
    assert barrier_plan.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_barrier_plan_detail(admin_api_client, admin_user, create_barrier_plan):
    """
    Ensure we can soft-delete one barrier plan object.
    """
    barrier_plan = create_barrier_plan()
    response = admin_api_client.delete(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert BarrierPlan.objects.count() == 1

    deleted_barrier_plan = BarrierPlan.objects.get(id=str(barrier_plan.id))
    assert deleted_barrier_plan.id == barrier_plan.id
    assert not deleted_barrier_plan.is_active
    assert deleted_barrier_plan.deleted_by == admin_user
    assert deleted_barrier_plan.deleted_at


@pytest.mark.django_db
def test_get_deleted_barrier_plan_returns_not_found(admin_api_client, create_barrier_plan):
    barrier_plan = create_barrier_plan()
    response = admin_api_client.delete(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = admin_api_client.get(
        reverse("v1:barrierplan-detail", kwargs={"pk": barrier_plan.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# BarrierReal Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_barrier_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    barrier_real = BarrierRealFactory(location=location)
    response = api_client.get(reverse("v1:barrierreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(barrier_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_barrier_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    BarrierPlanFactory(location=location)
    response = api_client.get(reverse("v1:barrierreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("condition", Condition.VERY_GOOD, Condition.AVERAGE),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.COVERED),
        ("connection_type", ConnectionType.OPEN_OUT, ConnectionType.CLOSED),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.BIKE, LaneType.HEAVY),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.RIGHT, LocationSpecifier.MIDDLE),
        ("reflective", Reflective.YES, Reflective.RED_YELLOW),
    ),
)
@pytest.mark.django_db
def test__barrier_real_filtering__list(field_name, value, second_value):
    do_filtering_test(
        BarrierRealFactory,
        "v1:barrierreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.BARRIER))
def test__barrier_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    barrier_real = BarrierRealFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.pk}),
        data,
        format="json",
    )

    barrier_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert barrier_real.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__barrier_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    barrier_real = BarrierRealFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.pk}),
        data,
        format="json",
    )

    barrier_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert barrier_real.device_type != device_type


@pytest.mark.django_db
def test__barrier_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "road_name": "TestRoad",
        "device_type": TrafficControlDeviceTypeFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:barrierreal-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_barrier_reals(admin_api_client, create_barrier_real):
    """
    Ensure we can get all real barrier objects.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    count = 3
    for _ in range(count):
        bp = BarrierPlanFactory(plan=plan)
        create_barrier_real(barrier_plan=bp)

    response = admin_api_client.get(reverse("v1:barrierreal-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        barrier_real = BarrierReal.objects.get(id=result.get("id"))
        assert result.get("location") == barrier_real.location.ewkt
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_all_barrier_real__geojson(admin_api_client, create_barrier_real):
    """
    Ensure we can get all barrier real objects with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    count = 3
    for _ in range(count):
        bp = BarrierPlanFactory(plan=plan)
        create_barrier_real(barrier_plan=bp)

    response = admin_api_client.get(reverse("v1:barrierreal-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        barrier_real = BarrierReal.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(barrier_real.location.json)
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_barrier_real_detail(admin_api_client, create_barrier_real):
    """
    Ensure we can get one real barrier object.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    bp = get_barrier_plan(plan=plan)

    barrier_real = create_barrier_real(barrier_plan=bp)
    operation_1 = add_barrier_real_operation(barrier_real, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_barrier_real_operation(barrier_real, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_barrier_real_operation(barrier_real, operation_date=datetime.date(2020, 11, 10))

    response = admin_api_client.get(reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(barrier_real.id)
    assert barrier_real.location.ewkt == response.data.get("location")
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"

    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response.data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]


@pytest.mark.django_db
def test_get_barrier_real_detail__geojson(admin_api_client, create_barrier_real):
    """
    Ensure we can get one real barrier object with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    bp = get_barrier_plan(plan=plan)

    barrier_real = create_barrier_real(barrier_plan=bp)
    response = admin_api_client.get(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(barrier_real.id)
    barrier_real_geojson = GeoJsonDict(barrier_real.location.json)
    assert barrier_real_geojson == response.data.get("location")
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_create_barrier_real(admin_api_client, admin_user, test_device_type, test_owner):
    """
    Ensure we can create a new real barrier object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "installation_date": "2020-01-02",
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "road_name": "Test street 1",
    }
    response = admin_api_client.post(reverse("v1:barrierreal-list"), data, format="json")
    barrier_real = BarrierReal.objects.first()
    logs = LogEntry.objects.get_for_object(barrier_real)
    assert logs.count() == 1
    log_entry = logs.latest()
    assert log_entry.action == LogEntry.Action.CREATE
    assert log_entry.actor == admin_user

    assert response.status_code == status.HTTP_201_CREATED
    assert BarrierReal.objects.count() == 1
    assert response.data.get("location") == data["location"]

    barrier_real = BarrierReal.objects.first()
    assert barrier_real.device_type.id == data["device_type"]
    assert barrier_real.location.ewkt == data["location"]
    assert barrier_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert barrier_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_create_barrier_real_existing_with_plan(admin_api_client, test_device_type, test_owner):
    """
    Test that BarrierReal API does not create a new db row when
    barrier with the same plan already exists
    """
    barrier_plan = BarrierPlanFactory()
    BarrierRealFactory(barrier_plan=barrier_plan)
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "road_name": "Test street 1",
        "barrier_plan": str(barrier_plan.pk),
    }
    response = admin_api_client.post(reverse("v1:barrierreal-list"), data, format="json")
    response_data = response.json()

    assert BarrierReal.objects.count() == 1
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "duplicate key value violates unique constraint" in response_data["detail"]
    assert "traffic_control_barrierreal_unique_barrier_plan" in response_data["detail"]


@pytest.mark.django_db
def test_update_barrier_real(admin_api_client, test_device_type, test_owner, create_barrier_real):
    """
    Ensure we can update existing real barrier object.
    """
    barrier_real = create_barrier_real()
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "installation_date": "2020-01-21",
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "road_name": "Test street 1",
    }
    response = admin_api_client.put(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert BarrierReal.objects.count() == 1

    barrier_real = BarrierReal.objects.first()
    assert barrier_real.device_type.id == data["device_type"]
    assert barrier_real.location.ewkt == data["location"]
    assert barrier_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert barrier_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_barrier_real_detail(admin_api_client, admin_user, create_barrier_real):
    """
    Ensure we can soft-delete one real barrier object.
    """
    barrier_real = create_barrier_real()
    logs = LogEntry.objects.get_for_object(barrier_real)
    assert logs.count() == 1
    log_entry = logs.latest()
    assert log_entry.action == LogEntry.Action.CREATE
    assert log_entry.actor is None

    response = admin_api_client.delete(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert BarrierPlan.objects.count() == 1

    deleted_barrier_real = BarrierReal.objects.get(id=str(barrier_real.id))
    assert deleted_barrier_real.id == barrier_real.id
    assert not deleted_barrier_real.is_active
    assert deleted_barrier_real.deleted_by == admin_user
    assert deleted_barrier_real.deleted_at

    logs = LogEntry.objects.get_for_object(deleted_barrier_real)
    assert logs.count() == 2
    log_entry = logs.latest()
    assert log_entry.action == LogEntry.Action.UPDATE
    assert log_entry.actor == admin_user


@pytest.mark.django_db
def test_get_deleted_barrier_real_returns_not_found(admin_api_client, create_barrier_real):
    barrier_real = create_barrier_real()
    response = admin_api_client.delete(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = admin_api_client.get(
        reverse("v1:barrierreal-detail", kwargs={"pk": barrier_real.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_operation_barrier_real(admin_api_client, create_barrier_real):
    barrier_real = create_barrier_real()
    operation_type = get_operation_type()
    data = {
        "operation_date": "2020-01-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse("barrier-real-operations-list", kwargs={"barrier_real_pk": barrier_real.pk})
    response = admin_api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert barrier_real.operations.all().count() == 1


@pytest.mark.django_db
def test_update_operation_barrier_real(admin_api_client, create_barrier_real):
    barrier_real = create_barrier_real()
    operation_type = get_operation_type()
    operation = add_barrier_real_operation(
        barrier_real=barrier_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {
        "operation_date": "2020-02-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse(
        "barrier-real-operations-detail",
        kwargs={"barrier_real_pk": barrier_real.pk, "pk": operation.pk},
    )
    response = admin_api_client.put(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert barrier_real.operations.all().count() == 1
    assert barrier_real.operations.all().first().operation_date == datetime.date(2020, 2, 1)


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
def test__barrier_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    barrier = get_barrier_plan(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": barrier.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:barrierplan-{view_type}", kwargs=kwargs)
    data = {"location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert BarrierPlan.objects.count() == 1
    assert BarrierPlan.objects.first().is_active
    assert BarrierPlan.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__barrier_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    barrier = BarrierRealFactory(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": barrier.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:barrierreal-{view_type}", kwargs=kwargs)
    data = {"location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)"}

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert BarrierReal.objects.count() == 1
    assert BarrierReal.objects.first().is_active
    assert BarrierReal.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__barrier_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    barrier = BarrierRealFactory()
    operation_type = get_operation_type()
    operation = add_barrier_real_operation(
        barrier_real=barrier,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"barrier_real_pk": barrier.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"barrier-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert barrier.operations.all().count() == 1
    assert barrier.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
