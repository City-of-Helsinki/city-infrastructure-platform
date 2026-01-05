from typing import Callable

import pytest
from django.urls import reverse

from city_furniture.tests.factories import (
    FurnitureSignpostPlanFactory,
    FurnitureSignpostRealFactory,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    BarrierPlanFactory,
    BarrierRealFactory,
    get_api_client,
    MountPlanFactory,
    MountRealFactory,
    PlanFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficLightPlanFactory,
    TrafficLightRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)


def validate_dict(object: dict, validate_keys: Callable[[dict], None]):
    """
    Recursively validate nested dicts and lists of dicts with function `validate_keys`
    """
    validate_keys(object)

    for _, value in object.items():
        if isinstance(value, dict):
            validate_dict(value, validate_keys)

        elif isinstance(value, list):
            for list_item in value:
                if isinstance(list_item, dict):
                    validate_dict(list_item, validate_keys)


def assert_no_user_ids(object: dict):
    assert object.get("created_by") is None
    assert object.get("updated_by") is None
    assert object.get("deleted_by") is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint_name,device_factory",
    (
        ("v1:additionalsignplan", AdditionalSignPlanFactory),
        ("v1:additionalsignreal", AdditionalSignRealFactory),
        ("v1:barrierplan", BarrierPlanFactory),
        ("v1:barrierreal", BarrierRealFactory),
        ("v1:mountplan", MountPlanFactory),
        ("v1:mountreal", MountRealFactory),
        ("v1:plan", PlanFactory),
        ("v1:roadmarkingplan", RoadMarkingPlanFactory),
        ("v1:roadmarkingreal", RoadMarkingRealFactory),
        ("v1:signpostplan", SignpostPlanFactory),
        ("v1:signpostreal", SignpostRealFactory),
        ("v1:trafficlightplan", TrafficLightPlanFactory),
        ("v1:trafficlightreal", TrafficLightRealFactory),
        ("v1:trafficsignplan", TrafficSignPlanFactory),
        ("v1:trafficsignreal", TrafficSignRealFactory),
        ("v1:furnituresignpostplan", FurnitureSignpostPlanFactory),
        ("v1:furnituresignpostreal", FurnitureSignpostRealFactory),
    ),
)
def test__hide_user_info_from_anonymous_request_single(
    endpoint_name: str,
    device_factory: Callable,
):
    client = get_api_client()
    device_object = device_factory()

    endpoint = f"{endpoint_name}-detail"

    response = client.get(reverse(endpoint, kwargs={"pk": device_object.id}))
    response_data = response.json()

    validate_dict(response_data, assert_no_user_ids)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint_name,device_factory",
    (
        ("v1:additionalsignplan", AdditionalSignPlanFactory),
        ("v1:additionalsignreal", AdditionalSignRealFactory),
        ("v1:barrierplan", BarrierPlanFactory),
        ("v1:barrierreal", BarrierRealFactory),
        ("v1:mountplan", MountPlanFactory),
        ("v1:mountreal", MountRealFactory),
        ("v1:plan", PlanFactory),
        ("v1:roadmarkingplan", RoadMarkingPlanFactory),
        ("v1:roadmarkingreal", RoadMarkingRealFactory),
        ("v1:signpostplan", SignpostPlanFactory),
        ("v1:signpostreal", SignpostRealFactory),
        ("v1:trafficlightplan", TrafficLightPlanFactory),
        ("v1:trafficlightreal", TrafficLightRealFactory),
        ("v1:trafficsignplan", TrafficSignPlanFactory),
        ("v1:trafficsignreal", TrafficSignRealFactory),
        ("v1:furnituresignpostplan", FurnitureSignpostPlanFactory),
        ("v1:furnituresignpostreal", FurnitureSignpostRealFactory),
    ),
)
def test__hide_user_info_from_anonymous_request_list(
    endpoint_name: str,
    device_factory: Callable,
):
    client = get_api_client()
    device_factory()

    endpoint = f"{endpoint_name}-list"

    response = client.get(reverse(endpoint))
    response_data = response.json()
    devices = response_data["results"]

    assert len(devices) == 1
    for device in devices:
        validate_dict(device, assert_no_user_ids)
