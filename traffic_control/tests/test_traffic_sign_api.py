import datetime
import json
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import (
    Condition,
    DeviceTypeTargetModel,
    InstallationStatus,
    LaneNumber,
    LaneType,
    Lifecycle,
    Reflection,
    Size,
    Surface,
)
from traffic_control.models import TrafficSignPlan, TrafficSignReal
from traffic_control.models.traffic_sign import LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_traffic_sign_real_operation,
    get_api_client,
    get_operation_type,
    get_owner,
    get_traffic_sign_plan,
    get_user,
    OwnerFactory,
    PlanFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.test_base_api import illegal_test_point
from traffic_control.tests.test_base_api_3d import (
    point_location_error_test_data_3d,
    point_location_test_data_3d,
    test_point_3d,
)
from traffic_control.tests.utils import MIN_X, MIN_Y

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def create_traffic_sign_plan(admin_user, test_device_type, test_owner):
    def _create(**overrides):
        defaults = {
            "device_type": test_device_type,
            "location": test_point_3d,
            "lifecycle": Lifecycle.ACTIVE,
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
            "peak_fastened": False,
            "double_sided": False,
        }
        defaults.update(overrides)
        return TrafficSignPlanFactory(**defaults)

    return _create


@pytest.fixture
def create_traffic_sign_real(admin_user, test_device_type, test_owner, create_traffic_sign_plan):
    def _create(traffic_sign_plan=None, **overrides):
        if traffic_sign_plan is None:
            traffic_sign_plan = create_traffic_sign_plan()

        defaults = {
            "traffic_sign_plan": traffic_sign_plan,
            "device_type": test_device_type,
            "location": test_point_3d,
            "installation_date": datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            "lifecycle": Lifecycle.ACTIVE,
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return TrafficSignRealFactory(**defaults)

    return _create


# ==============================================================================
# TrafficSignPlan Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data_3d)
def test_filter_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_plan = get_traffic_sign_plan(location)
    response = api_client.get(reverse("v1:trafficsignplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data_3d,
)
def test_filter_error_traffic_sign_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    get_traffic_sign_plan(location)
    response = api_client.get(reverse("v1:trafficsignplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.ABOVE, LocationSpecifier.RIGHT),
        ("reflection_class", Reflection.R1, Reflection.R3),
        ("size", Size.LARGE, Size.SMALL),
        ("surface_class", Surface.FLAT, Surface.CONVEX),
    ),
)
@pytest.mark.django_db
def test__traffic_sign_plans_filtering__list(field_name, value, second_value):
    do_filtering_test(
        TrafficSignPlanFactory,
        "v1:trafficsignplan-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_SIGN))
def test__traffic_sign_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_plan = get_traffic_sign_plan()
    device_type = TrafficControlDeviceTypeFactory(
        code="123", description="test", target_model=target_model, value="12.5"
    )
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.pk}),
        data,
        format="json",
    )

    traffic_sign_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_sign_plan.device_type == device_type
    assert traffic_sign_plan.value == Decimal("12.5")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
    ),
)
def test__traffic_sign_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_plan = get_traffic_sign_plan()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.pk}),
        data,
        format="json",
    )

    traffic_sign_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_sign_plan.device_type != device_type


@pytest.mark.django_db
def test__traffic_sign_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "device_type": TrafficControlDeviceTypeFactory(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN).pk,
    }
    do_illegal_geometry_test(
        "v1:trafficsignplan-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_traffic_sign_plans(admin_api_client, create_traffic_sign_plan):
    """
    Ensure we can get all traffic sign plan objects.
    """
    count = 3
    for _ in range(count):
        create_traffic_sign_plan()
    response = admin_api_client.get(reverse("v1:trafficsignplan-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        traffic_sign_plan = TrafficSignPlan.objects.get(id=result.get("id"))
        assert result.get("location") == traffic_sign_plan.location.ewkt


@pytest.mark.django_db
def test_get_all_traffic_sign_plans__geojson(admin_api_client, create_traffic_sign_plan):
    """
    Ensure we can get all traffic sign plan objects with GeoJSON location.
    """
    count = 3
    for _ in range(count):
        create_traffic_sign_plan()
    response = admin_api_client.get(reverse("v1:trafficsignplan-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        traffic_sign_plan = TrafficSignPlan.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(traffic_sign_plan.location.json)


@pytest.mark.django_db
def test_get_traffic_sign_plan_detail(admin_api_client, create_traffic_sign_plan):
    """
    Ensure we can get one traffic sign plan object.
    """
    traffic_sign_plan = create_traffic_sign_plan()
    response = admin_api_client.get(reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(traffic_sign_plan.id)
    assert traffic_sign_plan.location.ewkt == response.data.get("location")


@pytest.mark.django_db
def test_get_traffic_sign_plan_detail__geojson(admin_api_client, create_traffic_sign_plan):
    """
    Ensure we can get one traffic sign plan object with GeoJSON location.
    """
    traffic_sign_plan = create_traffic_sign_plan()
    response = admin_api_client.get(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(traffic_sign_plan.id)
    traffic_sign_plan_geojson = GeoJsonDict(traffic_sign_plan.location.json)
    assert traffic_sign_plan_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_traffic_sign_plan(admin_api_client, test_device_type, test_owner):
    """
    Ensure we can create a new traffic sign plan object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point_3d.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
    }
    response = admin_api_client.post(reverse("v1:trafficsignplan-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert TrafficSignPlan.objects.count() == 1
    assert response.data.get("location") == data["location"]
    traffic_sign_plan = TrafficSignPlan.objects.first()
    assert traffic_sign_plan.device_type.id == data["device_type"]
    assert traffic_sign_plan.location.ewkt == data["location"]
    assert traffic_sign_plan.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_create_traffic_sign_real_with_existing_plan(admin_api_client, test_device_type, test_owner):
    ts_plan = TrafficSignPlanFactory()
    TrafficSignRealFactory(traffic_sign_plan=ts_plan)
    data = {
        "device_type": test_device_type.id,
        "location": test_point_3d.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "traffic_sign_plan": ts_plan.id,
    }
    response = admin_api_client.post(reverse("v1:trafficsignreal-list"), data, format="json")
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert TrafficSignReal.objects.count() == 1
    assert "duplicate key value violates unique constraint" in response_data["detail"]
    assert "traffic_control_trafficsignreal_unique_traffic_sign_plan" in response_data["detail"]


@pytest.mark.django_db
def test_update_traffic_sign_plan(admin_api_client, test_device_type_2, test_owner, create_traffic_sign_plan):
    """
    Ensure we can update existing traffic sign plan object.
    """
    traffic_sign_plan = create_traffic_sign_plan()
    data = {
        "device_type": test_device_type_2.id,
        "location": test_point_3d.ewkt,
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "peak_fastened": True,
        "double_sided": True,
    }
    response = admin_api_client.put(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert TrafficSignPlan.objects.count() == 1
    traffic_sign_plan = TrafficSignPlan.objects.first()
    assert traffic_sign_plan.device_type.id == data["device_type"]
    assert traffic_sign_plan.location.ewkt == data["location"]
    assert traffic_sign_plan.lifecycle.value == data["lifecycle"]
    assert traffic_sign_plan.peak_fastened is True
    assert traffic_sign_plan.double_sided is True


@pytest.mark.django_db
def test_delete_traffic_sign_plan_detail(admin_api_client, admin_user, create_traffic_sign_plan):
    """
    Ensure we can soft-delete one traffic sign plan object.
    """
    traffic_sign_plan = create_traffic_sign_plan()
    response = admin_api_client.delete(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert TrafficSignPlan.objects.count() == 1
    deleted_traffic_sign_plan = TrafficSignPlan.objects.get(id=str(traffic_sign_plan.id))
    assert deleted_traffic_sign_plan.id == traffic_sign_plan.id
    assert not deleted_traffic_sign_plan.is_active
    assert deleted_traffic_sign_plan.deleted_by == admin_user
    assert deleted_traffic_sign_plan.deleted_at


@pytest.mark.django_db
def test_get_deleted_traffic_sign_plan_returns_not_found(admin_api_client, create_traffic_sign_plan):
    traffic_sign_plan = create_traffic_sign_plan()
    response = admin_api_client.delete(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:trafficsignplan-detail", kwargs={"pk": traffic_sign_plan.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# TrafficSignReal Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize("location,location_query,expected", point_location_test_data_3d)
def test_filter_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    traffic_sign_real = TrafficSignRealFactory(location=location)
    response = api_client.get(reverse("v1:trafficsignreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(traffic_sign_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    point_location_error_test_data_3d,
)
def test_filter_error_traffic_sign_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    TrafficSignRealFactory(location=location)
    response = api_client.get(reverse("v1:trafficsignreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("condition", Condition.VERY_GOOD, Condition.GOOD),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.MISSING),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("location_specifier", LocationSpecifier.ABOVE, LocationSpecifier.RIGHT),
        ("reflection_class", Reflection.R1, Reflection.R3),
        ("size", Size.LARGE, Size.SMALL),
        ("surface_class", Surface.FLAT, Surface.CONVEX),
    ),
)
@pytest.mark.django_db
def test__traffic_sign_reals_filtering__list(field_name, value, second_value):
    do_filtering_test(
        TrafficSignRealFactory,
        "v1:trafficsignreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.TRAFFIC_SIGN))
def test__traffic_sign_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_real = TrafficSignRealFactory()
    device_type = TrafficControlDeviceTypeFactory(
        code="123", description="test", target_model=target_model, value="12.5"
    )
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.pk}),
        data,
        format="json",
    )

    traffic_sign_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert traffic_sign_real.device_type == device_type
    assert traffic_sign_real.value == Decimal("12.5")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.ROAD_MARKING,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
    ),
)
def test__traffic_sign_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    traffic_sign_real = TrafficSignRealFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.pk}),
        data,
        format="json",
    )

    traffic_sign_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert traffic_sign_real.device_type != device_type


@pytest.mark.django_db
def test__traffic_sign_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "owner": OwnerFactory().pk,
        "device_type": TrafficControlDeviceTypeFactory(target_model=DeviceTypeTargetModel.TRAFFIC_SIGN).pk,
    }
    do_illegal_geometry_test(
        "v1:trafficsignreal-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_traffic_sign_reals(admin_api_client, create_traffic_sign_real):
    """
    Ensure we can get all traffic sign real objects.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    count = 3
    for _ in range(count):
        tsp = TrafficSignPlanFactory(plan=plan)
        create_traffic_sign_real(traffic_sign_plan=tsp)

    response = admin_api_client.get(reverse("v1:trafficsignreal-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        traffic_sign_real = TrafficSignReal.objects.get(id=result.get("id"))
        assert result.get("location") == traffic_sign_real.location.ewkt
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_all_traffic_sign_reals__geojson(admin_api_client, create_traffic_sign_real):
    """
    Ensure we can get all traffic sign real objects with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    count = 3
    for _ in range(count):
        tsp = TrafficSignPlanFactory(plan=plan)
        create_traffic_sign_real(traffic_sign_plan=tsp)

    response = admin_api_client.get(reverse("v1:trafficsignreal-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        traffic_sign_real = TrafficSignReal.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(traffic_sign_real.location.json)
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_traffic_sign_real_detail(admin_api_client, create_traffic_sign_real):
    """
    Ensure we can get one traffic sign real object.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    tsp = get_traffic_sign_plan(plan=plan)
    traffic_sign_real = create_traffic_sign_real(traffic_sign_plan=tsp)
    operation_1 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_traffic_sign_real_operation(traffic_sign_real, operation_date=datetime.date(2020, 11, 10))

    response = admin_api_client.get(reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(traffic_sign_real.id)
    assert traffic_sign_real.location.ewkt == response.data.get("location")
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"

    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response.data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]


@pytest.mark.django_db
def test_get_traffic_sign_real_detail__geojson(admin_api_client, create_traffic_sign_real):
    """
    Ensure we can get one traffic sign real object with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    tsp = get_traffic_sign_plan(plan=plan)
    traffic_sign_real = create_traffic_sign_real(traffic_sign_plan=tsp)

    response = admin_api_client.get(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(traffic_sign_real.id)
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"
    traffic_sign_real_geojson = GeoJsonDict(traffic_sign_real.location.json)
    assert traffic_sign_real_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_traffic_sign_real(admin_api_client, test_device_type, test_owner):
    """
    Ensure we can create a new traffic sign real object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point_3d.ewkt,
        "installation_date": "2020-01-02",
        "lifecycle": Lifecycle.ACTIVE.value,
        "installation_id": 123,
        "permit_decision_id": 456,
        "owner": test_owner.pk,
    }
    response = admin_api_client.post(reverse("v1:trafficsignreal-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert TrafficSignReal.objects.count() == 1
    assert response.data.get("location") == data["location"]
    traffic_sign_real = TrafficSignReal.objects.first()
    assert traffic_sign_real.device_type.id == data["device_type"]
    assert traffic_sign_real.location.ewkt == data["location"]
    assert traffic_sign_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert traffic_sign_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_update_traffic_sign_real(admin_api_client, test_device_type_2, test_owner, create_traffic_sign_real):
    """
    Ensure we can update existing traffic sign real object.
    """
    traffic_sign_real = create_traffic_sign_real()
    data = {
        "device_type": test_device_type_2.id,
        "location": test_point_3d.ewkt,
        "installation_date": "2020-01-03",
        "lifecycle": Lifecycle.INACTIVE.value,
        "installation_id": 123,
        "permit_decision_id": 456,
        "owner": test_owner.pk,
        "peak_fastened": True,
        "double_sided": True,
    }
    response = admin_api_client.put(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert TrafficSignReal.objects.count() == 1
    traffic_sign_real = TrafficSignReal.objects.first()
    assert traffic_sign_real.device_type.id == data["device_type"]
    assert traffic_sign_real.location.ewkt == data["location"]
    assert traffic_sign_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert traffic_sign_real.lifecycle.value == data["lifecycle"]
    assert traffic_sign_real.peak_fastened is True
    assert traffic_sign_real.double_sided is True


@pytest.mark.django_db
def test_delete_traffic_sign_real_detail(admin_api_client, admin_user, create_traffic_sign_real):
    """
    Ensure we can soft-delete one traffic sign real object.
    """
    traffic_sign_real = create_traffic_sign_real()
    response = admin_api_client.delete(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert TrafficSignReal.objects.count() == 1
    deleted_traffic_sign_real = TrafficSignReal.objects.get(id=str(traffic_sign_real.id))
    assert deleted_traffic_sign_real.id == traffic_sign_real.id
    assert not deleted_traffic_sign_real.is_active
    assert deleted_traffic_sign_real.deleted_by == admin_user
    assert deleted_traffic_sign_real.deleted_at


@pytest.mark.django_db
def test_get_deleted_traffic_sign_real_returns_not_found(admin_api_client, create_traffic_sign_real):
    traffic_sign_real = create_traffic_sign_real()
    response = admin_api_client.delete(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:trafficsignreal-detail", kwargs={"pk": traffic_sign_real.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_operation_traffic_sign_real(admin_api_client, create_traffic_sign_real):
    traffic_sign_real = create_traffic_sign_real()
    operation_type = get_operation_type()
    data = {
        "operation_date": "2020-01-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse("traffic-sign-real-operations-list", kwargs={"traffic_sign_real_pk": traffic_sign_real.pk})
    response = admin_api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert traffic_sign_real.operations.all().count() == 1


@pytest.mark.django_db
def test_update_operation_traffic_sign_real(admin_api_client, create_traffic_sign_real):
    traffic_sign_real = create_traffic_sign_real()
    operation_type = get_operation_type()
    operation = add_traffic_sign_real_operation(
        traffic_sign_real=traffic_sign_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {
        "operation_date": "2020-02-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse(
        "traffic-sign-real-operations-detail",
        kwargs={"traffic_sign_real_pk": traffic_sign_real.pk, "pk": operation.pk},
    )
    response = admin_api_client.put(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert traffic_sign_real.operations.all().count() == 1
    assert traffic_sign_real.operations.all().first().operation_date == datetime.date(2020, 2, 1)


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
def test__traffic_sign_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_sign = get_traffic_sign_plan(location=f"SRID=3879;POINT Z ({MIN_X + 1} {MIN_Y + 1} 0)")
    kwargs = {"pk": traffic_sign.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:trafficsignplan-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X + 2} {MIN_Y + 2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert TrafficSignPlan.objects.count() == 1
    assert TrafficSignPlan.objects.first().is_active
    assert TrafficSignPlan.objects.first().location == f"SRID=3879;POINT Z ({MIN_X + 1} {MIN_Y + 1} 0)"
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
def test__traffic_sign_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_sign = TrafficSignRealFactory(location=f"SRID=3879;POINT Z ({MIN_X + 1} {MIN_Y + 1} 0)")
    kwargs = {"pk": traffic_sign.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:trafficsignreal-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X + 2} {MIN_Y + 2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert TrafficSignReal.objects.count() == 1
    assert TrafficSignReal.objects.first().is_active
    assert TrafficSignReal.objects.first().location == f"SRID=3879;POINT Z ({MIN_X + 1} {MIN_Y + 1} 0)"
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
def test__traffic_sign_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    traffic_sign = TrafficSignRealFactory()
    operation_type = get_operation_type()
    operation = add_traffic_sign_real_operation(
        traffic_sign_real=traffic_sign,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": operation_type.pk}

    kwargs = {"traffic_sign_real_pk": traffic_sign.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"traffic-sign-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, data)

    assert traffic_sign.operations.all().count() == 1
    assert traffic_sign.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
