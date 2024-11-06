from typing import Callable

import pytest
from django.urls import reverse

from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_additional_sign_plan,
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_plan,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
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
        ("v1:additionalsignplan", get_additional_sign_plan),
        ("v1:additionalsignreal", AdditionalSignRealFactory),
        ("v1:barrierplan", get_barrier_plan),
        ("v1:barrierreal", get_barrier_real),
        ("v1:mountplan", get_mount_plan),
        ("v1:mountreal", get_mount_real),
        ("v1:plan", get_plan),
        ("v1:roadmarkingplan", get_road_marking_plan),
        ("v1:roadmarkingreal", get_road_marking_real),
        ("v1:signpostplan", get_signpost_plan),
        ("v1:signpostreal", get_signpost_real),
        ("v1:trafficlightplan", get_traffic_light_plan),
        ("v1:trafficlightreal", get_traffic_light_real),
        ("v1:trafficsignplan", get_traffic_sign_plan),
        ("v1:trafficsignreal", get_traffic_sign_real),
        ("v1:furnituresignpostplan", get_furniture_signpost_plan),
        ("v1:furnituresignpostreal", get_furniture_signpost_real),
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
        ("v1:additionalsignplan", get_additional_sign_plan),
        ("v1:additionalsignreal", AdditionalSignRealFactory),
        ("v1:barrierplan", get_barrier_plan),
        ("v1:barrierreal", get_barrier_real),
        ("v1:mountplan", get_mount_plan),
        ("v1:mountreal", get_mount_real),
        ("v1:plan", get_plan),
        ("v1:roadmarkingplan", get_road_marking_plan),
        ("v1:roadmarkingreal", get_road_marking_real),
        ("v1:signpostplan", get_signpost_plan),
        ("v1:signpostreal", get_signpost_real),
        ("v1:trafficlightplan", get_traffic_light_plan),
        ("v1:trafficlightreal", get_traffic_light_real),
        ("v1:trafficsignplan", get_traffic_sign_plan),
        ("v1:trafficsignreal", get_traffic_sign_real),
        ("v1:furnituresignpostplan", get_furniture_signpost_plan),
        ("v1:furnituresignpostreal", get_furniture_signpost_real),
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
