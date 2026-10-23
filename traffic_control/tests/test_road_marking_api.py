import datetime
import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_gis.fields import GeoJsonDict

from traffic_control.enums import Condition, DeviceTypeTargetModel, InstallationStatus, LaneNumber, LaneType, Lifecycle
from traffic_control.models import ArrowDirection, LineDirection, RoadMarkingColor, RoadMarkingPlan, RoadMarkingReal
from traffic_control.models.road_marking import LocationSpecifier
from traffic_control.tests.api_utils import do_filtering_test, do_illegal_geometry_test
from traffic_control.tests.factories import (
    add_road_marking_real_operation,
    get_api_client,
    get_operation_type,
    get_owner,
    get_road_marking_plan,
    get_user,
    OwnerFactory,
    PlanFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
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
# Fixtures
# ==============================================================================


@pytest.fixture
def create_road_marking_plan(admin_user, test_device_type, test_owner):
    def _create(**overrides):
        defaults = {
            "device_type": test_device_type,
            "value": "30",
            "color": RoadMarkingColor.WHITE,
            "location": test_point,
            "lifecycle": Lifecycle.ACTIVE,
            "material": "Maali",
            "is_grinded": True,
            "is_raised": False,
            "road_name": "Testingroad",
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return RoadMarkingPlan.objects.create(**defaults)

    return _create


@pytest.fixture
def create_road_marking_real(admin_user, test_device_type, test_owner, create_road_marking_plan):
    def _create(road_marking_plan=None, **overrides):
        if road_marking_plan is None:
            road_marking_plan = create_road_marking_plan()

        defaults = {
            "device_type": test_device_type,
            "road_marking_plan": road_marking_plan,
            "value": "30",
            "color": RoadMarkingColor.WHITE,
            "location": test_point,
            "installation_date": datetime.datetime.strptime("01012020", "%d%m%Y").date(),
            "lifecycle": Lifecycle.ACTIVE,
            "material": "Maali",
            "is_grinded": True,
            "is_raised": False,
            "road_name": "Testingroad",
            "owner": test_owner,
            "created_by": admin_user,
            "updated_by": admin_user,
        }
        defaults.update(overrides)
        return RoadMarkingReal.objects.create(**defaults)

    return _create


# ==============================================================================
# RoadMarkingPlan Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_road_markings_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    road_marking_plan = RoadMarkingPlanFactory(location=location)
    response = api_client.get(reverse("v1:roadmarkingplan-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(road_marking_plan.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_road_markings_plans_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    RoadMarkingPlanFactory(location=location)
    response = api_client.get(reverse("v1:roadmarkingplan-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("arrow_direction", ArrowDirection.RIGHT, ArrowDirection.RIGHT_AND_LEFT),
        ("color", RoadMarkingColor.WHITE, RoadMarkingColor.YELLOW),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("line_direction", LineDirection.FORWARD, LineDirection.BACKWARD),
        ("location_specifier", LocationSpecifier.BOTH_SIDES_OF_ROAD, LocationSpecifier.BOTH_SIDES_OF_LANE),
    ),
)
@pytest.mark.django_db
def test__road_marking_plan_filtering__list(field_name, value, second_value):
    do_filtering_test(
        RoadMarkingPlanFactory,
        "v1:roadmarkingplan-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.ROAD_MARKING))
def test__road_marking_plan__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_plan = RoadMarkingPlanFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking_plan.pk}),
        data,
        format="json",
    )

    road_marking_plan.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert road_marking_plan.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__road_marking_plan__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_plan = RoadMarkingPlanFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking_plan.pk}),
        data,
        format="json",
    )

    road_marking_plan.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert road_marking_plan.device_type != device_type


@pytest.mark.django_db
def test__road_marking_plan__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "name": "TestName",
        "owner": OwnerFactory().pk,
        "device_type": TrafficControlDeviceTypeFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:roadmarkingplan-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_road_markings(admin_api_client, create_road_marking_plan):
    """
    Ensure we can get all road marking plan objects.
    """
    count = 3
    for _ in range(count):
        create_road_marking_plan()
    response = admin_api_client.get(reverse("v1:roadmarkingplan-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        road_marking_plan = RoadMarkingPlan.objects.get(id=result.get("id"))
        assert result.get("location") == road_marking_plan.location.ewkt


@pytest.mark.django_db
def test_get_all_road_markings__geojson(admin_api_client, create_road_marking_plan):
    """
    Ensure we can get all road marking plan objects with GeoJSON location.
    """
    count = 3
    for _ in range(count):
        create_road_marking_plan()
    response = admin_api_client.get(reverse("v1:roadmarkingplan-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        road_marking_plan = RoadMarkingPlan.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(road_marking_plan.location.json)


@pytest.mark.django_db
def test_get_road_marking_detail(admin_api_client, create_road_marking_plan):
    """
    Ensure we can get one road marking plan object.
    """
    road_marking = create_road_marking_plan()
    response = admin_api_client.get(reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(road_marking.id)
    assert road_marking.location.ewkt == response.data.get("location")


@pytest.mark.django_db
def test_get_road_marking_detail__geojson(admin_api_client, create_road_marking_plan):
    """
    Ensure we can get one road marking plan object with GeoJSON location.
    """
    road_marking = create_road_marking_plan()
    response = admin_api_client.get(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(road_marking.id)
    road_marking_geojson = GeoJsonDict(road_marking.location.json)
    assert road_marking_geojson == response.data.get("location")


@pytest.mark.django_db
def test_create_road_marking(admin_api_client, test_device_type, test_owner):
    """
    Ensure we can create a new road marking plan object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "source_name": "test-source",
        "source_id": 1,
    }
    response = admin_api_client.post(reverse("v1:roadmarkingplan-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert RoadMarkingPlan.objects.count() == 1
    assert response.data.get("location") == data["location"]
    road_marking = RoadMarkingPlan.objects.first()
    assert road_marking.device_type.id == data["device_type"]
    assert road_marking.location.ewkt == data["location"]
    assert road_marking.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_update_road_marking(admin_api_client, test_device_type_2, test_owner, create_road_marking_plan):
    """
    Ensure we can update existing road marking plan object.
    """
    road_marking = create_road_marking_plan()
    data = {
        "device_type": test_device_type_2.id,
        "location": test_point.ewkt,
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "source_name": "test-source",
        "source_id": 1,
    }
    response = admin_api_client.put(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert RoadMarkingPlan.objects.count() == 1
    road_marking = RoadMarkingPlan.objects.first()
    assert road_marking.device_type.id == data["device_type"]
    assert road_marking.location.ewkt == data["location"]
    assert road_marking.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_road_marking_detail(admin_api_client, admin_user, create_road_marking_plan):
    """
    Ensure we can soft-delete one road marking plan object.
    """
    road_marking = create_road_marking_plan()
    response = admin_api_client.delete(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert RoadMarkingPlan.objects.count() == 1
    deleted_road_marking = RoadMarkingPlan.objects.get(id=str(road_marking.id))
    assert deleted_road_marking.id == road_marking.id
    assert not deleted_road_marking.is_active
    assert deleted_road_marking.deleted_by == admin_user
    assert deleted_road_marking.deleted_at


@pytest.mark.django_db
def test_get_deleted_road_marking_return_not_found(admin_api_client, create_road_marking_plan):
    road_marking = create_road_marking_plan()
    response = admin_api_client.delete(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:roadmarkingplan-detail", kwargs={"pk": road_marking.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# RoadMarkingReal Tests
# ==============================================================================


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_test_data, *line_location_test_data],
)
def test_filter_road_markings_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    road_marking_real = RoadMarkingRealFactory(location=location)
    response = api_client.get(reverse("v1:roadmarkingreal-list"), {"location": location_query.ewkt})

    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == expected

    if expected == 1:
        data = response.data.get("results")[0]
        assert str(road_marking_real.id) == data.get("id")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,location_query,expected",
    [*point_location_error_test_data, *line_location_error_test_data],
)
def test_filter_error_road_markings_reals_location(location, location_query, expected):
    """
    Ensure that filtering with location is working correctly.
    """
    api_client = get_api_client()

    RoadMarkingRealFactory(location=location)
    response = api_client.get(reverse("v1:roadmarkingreal-list"), {"location": location_query})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get("location")[0] == expected


@pytest.mark.parametrize(
    "field_name,value,second_value",
    (
        ("arrow_direction", ArrowDirection.RIGHT, ArrowDirection.RIGHT_AND_LEFT),
        ("color", RoadMarkingColor.WHITE, RoadMarkingColor.YELLOW),
        ("condition", Condition.VERY_GOOD, Condition.AVERAGE),
        ("installation_status", InstallationStatus.IN_USE, InstallationStatus.COVERED),
        ("lane_number", LaneNumber.ADDITIONAL_LEFT_1, LaneNumber.ADDITIONAL_LEFT_2),
        ("lane_type", LaneType.HEAVY, LaneType.BIKE),
        ("lifecycle", Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE),
        ("line_direction", LineDirection.FORWARD, LineDirection.BACKWARD),
        ("location_specifier", LocationSpecifier.BOTH_SIDES_OF_ROAD, LocationSpecifier.BOTH_SIDES_OF_LANE),
    ),
)
@pytest.mark.django_db
def test__road_marking_reals_filtering__list(field_name, value, second_value):
    do_filtering_test(
        RoadMarkingRealFactory,
        "v1:roadmarkingreal-list",
        field_name,
        value,
        second_value,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target_model", (None, DeviceTypeTargetModel.ROAD_MARKING))
def test__road_marking_real__valid_device_type(target_model):
    """
    Ensure that device types with supported target_model value are allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_real = RoadMarkingRealFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.pk}),
        data,
        format="json",
    )

    road_marking_real.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert road_marking_real.device_type == device_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target_model",
    (
        DeviceTypeTargetModel.BARRIER,
        DeviceTypeTargetModel.SIGNPOST,
        DeviceTypeTargetModel.TRAFFIC_LIGHT,
        DeviceTypeTargetModel.TRAFFIC_SIGN,
    ),
)
def test__road_marking_real__invalid_device_type(target_model):
    """
    Ensure that device types with unsupported target_model value are not allowed.
    """
    client = get_api_client(user=get_user(admin=True))
    road_marking_real = RoadMarkingRealFactory()
    device_type = TrafficControlDeviceTypeFactory(code="123", description="test", target_model=target_model)
    data = {"device_type": device_type.id}

    response = client.patch(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.pk}),
        data,
        format="json",
    )

    road_marking_real.refresh_from_db()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert road_marking_real.device_type != device_type


@pytest.mark.django_db
def test__road_marking_real__create_with_invalid_geometry():
    data = {
        "location": illegal_test_point.ewkt,
        "name": "TestName",
        "owner": OwnerFactory().pk,
        "device_type": TrafficControlDeviceTypeFactory().pk,
    }
    do_illegal_geometry_test(
        "v1:roadmarkingreal-list",
        data,
        ["The location falls outside the city's boundaries."],
    )


@pytest.mark.django_db
def test_get_all_road_marking_reals(admin_api_client, create_road_marking_real):
    """
    Ensure we can get all real road marking objects.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

    count = 3
    for _ in range(count):
        rmp = RoadMarkingPlanFactory(plan=plan)
        create_road_marking_real(road_marking_plan=rmp)
    response = admin_api_client.get(reverse("v1:roadmarkingreal-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        road_marking_real = RoadMarkingReal.objects.get(id=result.get("id"))
        assert result.get("location") == road_marking_real.location.ewkt
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_all_road_marking_reals__geojson(admin_api_client, create_road_marking_real):
    """
    Ensure we can get all real road marking objects with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")

    count = 3
    for _ in range(count):
        rmp = RoadMarkingPlanFactory(plan=plan)
        create_road_marking_real(road_marking_plan=rmp)
    response = admin_api_client.get(reverse("v1:roadmarkingreal-list"), data={"geo_format": "geojson"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("count") == count

    results = response.data.get("results")
    for result in results:
        road_marking_real = RoadMarkingReal.objects.get(id=result.get("id"))
        assert result.get("location") == GeoJsonDict(road_marking_real.location.json)
        assert result.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_get_road_marking_real_detail(admin_api_client, create_road_marking_real):
    """
    Ensure we can get one real road marking object.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    rmp = RoadMarkingPlanFactory(plan=plan)
    road_marking_real = create_road_marking_real(road_marking_plan=rmp)
    operation_1 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 5))
    operation_2 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 15))
    operation_3 = add_road_marking_real_operation(road_marking_real, operation_date=datetime.date(2020, 11, 10))
    response = admin_api_client.get(reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(road_marking_real.id)
    assert road_marking_real.location.ewkt == response.data.get("location")
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"

    # verify operations are ordered by operation_date
    operation_ids = [operation["id"] for operation in response.data["operations"]]
    assert operation_ids == [operation_1.id, operation_3.id, operation_2.id]


@pytest.mark.django_db
def test_get_road_marking_real_detail__geojson(admin_api_client, create_road_marking_real):
    """
    Ensure we can get one real road marking object with GeoJSON location.
    """
    plan = PlanFactory.create(decision_id="TEST-DECISION-ID")
    rmp = RoadMarkingPlanFactory(plan=plan)
    road_marking_real = create_road_marking_real(road_marking_plan=rmp)
    response = admin_api_client.get(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        data={"geo_format": "geojson"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get("id") == str(road_marking_real.id)
    road_marking_real_geojson = GeoJsonDict(road_marking_real.location.json)
    assert road_marking_real_geojson == response.data.get("location")
    assert response.data.get("plan_decision_id") == "TEST-DECISION-ID"


@pytest.mark.django_db
def test_create_road_marking_real(admin_api_client, admin_user, test_device_type, test_owner):
    """
    Ensure we can create a new real road marking object.
    """
    data = {
        "device_type": test_device_type.id,
        "location": test_point.ewkt,
        "installation_date": "2020-01-02",
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": test_owner.pk,
        "source_name": "test-source",
        "source_id": 1,
    }
    response = admin_api_client.post(reverse("v1:roadmarkingreal-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert RoadMarkingReal.objects.count() == 1
    assert response.data.get("location") == data["location"]
    road_marking_real = RoadMarkingReal.objects.first()
    assert road_marking_real.device_type.id == data["device_type"]
    assert road_marking_real.location.ewkt == data["location"]
    assert road_marking_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert road_marking_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_create_road_marking_real_with_existing_plan(admin_api_client, test_device_type_2, test_owner):
    rm_plan = RoadMarkingPlanFactory()
    RoadMarkingRealFactory(road_marking_plan=rm_plan)
    data = {
        "device_type": test_device_type_2.id,
        "location": test_point.ewkt,
        "installation_date": "2020-01-21",
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "source_name": "test-source",
        "source_id": 1,
        "road_marking_plan": rm_plan.id,
    }
    response = admin_api_client.post(reverse("v1:roadmarkingreal-list"), data, format="json")
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert RoadMarkingReal.objects.count() == 1
    assert "duplicate key value violates unique constraint" in response_data["detail"]
    assert "traffic_control_roadmarkingreal_unique_road_marking_plan_id" in response_data["detail"]


@pytest.mark.django_db
def test_update_road_marking_real(admin_api_client, test_device_type_2, test_owner, create_road_marking_real):
    """
    Ensure we can update existing real road marking object.
    """
    road_marking_real = create_road_marking_real()
    data = {
        "device_type": test_device_type_2.id,
        "location": test_point.ewkt,
        "installation_date": "2020-01-21",
        "lifecycle": Lifecycle.INACTIVE.value,
        "owner": test_owner.pk,
        "source_name": "test-source",
        "source_id": 1,
    }
    response = admin_api_client.put(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
        data,
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert RoadMarkingReal.objects.count() == 1
    road_marking_real = RoadMarkingReal.objects.first()
    assert road_marking_real.device_type.id == data["device_type"]
    assert road_marking_real.location.ewkt == data["location"]
    assert road_marking_real.installation_date.strftime("%Y-%m-%d") == data["installation_date"]
    assert road_marking_real.lifecycle.value == data["lifecycle"]


@pytest.mark.django_db
def test_delete_road_marking_real_detail(admin_api_client, admin_user, create_road_marking_real):
    """
    Ensure we can soft-delete one real road marking object.
    """
    road_marking_real = create_road_marking_real()
    response = admin_api_client.delete(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert RoadMarkingReal.objects.count() == 1
    deleted_road_marking_real = RoadMarkingReal.objects.get(id=str(road_marking_real.id))
    assert deleted_road_marking_real.id == road_marking_real.id
    assert not deleted_road_marking_real.is_active
    assert deleted_road_marking_real.deleted_by == admin_user
    assert deleted_road_marking_real.deleted_at


@pytest.mark.django_db
def test_get_deleted_road_marking_real_returns_not_found(admin_api_client, create_road_marking_real):
    road_marking_real = create_road_marking_real()
    response = admin_api_client.delete(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response = admin_api_client.get(
        reverse("v1:roadmarkingreal-detail", kwargs={"pk": road_marking_real.id}),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_create_operation_road_marking_real(admin_api_client, create_road_marking_real):
    road_marking_real = create_road_marking_real()
    operation_type = get_operation_type()
    data = {
        "operation_date": "2020-01-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse("road-marking-real-operations-list", kwargs={"road_marking_real_pk": road_marking_real.pk})
    response = admin_api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert road_marking_real.operations.all().count() == 1


@pytest.mark.django_db
def test_update_operation_road_marking_real(admin_api_client, create_road_marking_real):
    road_marking_real = create_road_marking_real()
    operation_type = get_operation_type()
    operation = add_road_marking_real_operation(
        road_marking_real=road_marking_real, operation_type=operation_type, operation_date=datetime.date(2020, 1, 1)
    )
    data = {
        "operation_date": "2020-02-01",
        "operation_type_id": operation_type.pk,
    }
    url = reverse(
        "road-marking-real-operations-detail",
        kwargs={"road_marking_real_pk": road_marking_real.pk, "pk": operation.pk},
    )
    response = admin_api_client.put(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert road_marking_real.operations.all().count() == 1
    assert road_marking_real.operations.all().first().operation_date == datetime.date(2020, 2, 1)


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
def test__road_marking_plan__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = get_road_marking_plan(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": road_marking.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:roadmarkingplan-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert RoadMarkingPlan.objects.count() == 1
    assert RoadMarkingPlan.objects.first().is_active
    assert RoadMarkingPlan.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__road_marking_real__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = RoadMarkingRealFactory(location=f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)")
    kwargs = {"pk": road_marking.pk} if view_type == "detail" else None
    resource_path = reverse(f"v1:roadmarkingreal-{view_type}", kwargs=kwargs)
    data = {
        "location": f"SRID=3879;POINT Z ({MIN_X+2} {MIN_Y+2} 0)",
        "device_type": str(TrafficControlDeviceTypeFactory().id),
        "owner": str(get_owner().id),
    }

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert RoadMarkingReal.objects.count() == 1
    assert RoadMarkingReal.objects.first().is_active
    assert RoadMarkingReal.objects.first().location == f"SRID=3879;POINT Z ({MIN_X+1} {MIN_Y+1} 0)"
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
def test__road_marking_real_operation__anonymous_user(method, expected_status, view_type):
    """
    Test that for unauthorized user the API responses 401 unauthorized, but OK for safe methods.
    """
    client = get_api_client(user=None)
    road_marking = RoadMarkingRealFactory()
    operation_type = get_operation_type()
    operation = add_road_marking_real_operation(
        road_marking_real=road_marking,
        operation_type=operation_type,
        operation_date=datetime.date(2020, 1, 1),
    )

    data = {"operation_date": "2020-02-01", "operation_type_id": str(operation_type.pk)}

    kwargs = {"road_marking_real_pk": road_marking.pk}
    if view_type == "detail":
        kwargs["pk"] = operation.pk

    resource_path = reverse(f"road-marking-real-operations-{view_type}", kwargs=kwargs)

    response = client.generic(method, resource_path, json.dumps(data), content_type="application/json")

    assert road_marking.operations.all().count() == 1
    assert road_marking.operations.all().first().operation_date == datetime.date(2020, 1, 1)
    assert response.status_code == expected_status
