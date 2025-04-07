import pytest
from django.urls import reverse
from rest_framework import status

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.tests.factories import get_city_furniture_device_type
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    Plan,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.tests.factories import (
    get_api_client,
    get_owner,
    get_user,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.test_base_api_3d import test_point_3d


def get_data_create_additional_sign():
    parent = TrafficSignRealFactory()
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
        "parent": parent.id,
    }


def get_data_create_additional_sign_plan():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
        "parent": TrafficSignPlanFactory().pk,
    }


def get_data_create_barrier():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
        "road_name": "Road name",
    }


def get_data_create_mount():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
    }


def get_data_create_plan():
    return {
        "name": "Plan name",
        "decision_id": "2024-0001",
    }


def get_data_create_road_marking():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
    }


def get_data_create_signpost():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
    }


def get_data_create_traffic_light():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
    }


def get_data_create_traffic_sign():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
    }


def get_data_create_furniture_signpost():
    return {
        "location": test_point_3d.ewkt,
        "owner": str(get_owner().id),
        "device_type": str(get_city_furniture_device_type().id),
    }


@pytest.mark.parametrize(
    "model, url_name, data_factory",
    (
        (AdditionalSignPlan, "additionalsignplan", get_data_create_additional_sign_plan),
        (AdditionalSignReal, "additionalsignreal", get_data_create_additional_sign),
        (BarrierPlan, "barrierplan", get_data_create_barrier),
        (BarrierReal, "barrierreal", get_data_create_barrier),
        (FurnitureSignpostPlan, "furnituresignpostplan", get_data_create_furniture_signpost),
        (FurnitureSignpostReal, "furnituresignpostreal", get_data_create_furniture_signpost),
        (MountPlan, "mountplan", get_data_create_mount),
        (MountReal, "mountreal", get_data_create_mount),
        (Plan, "plan", get_data_create_plan),
        (RoadMarkingPlan, "roadmarkingplan", get_data_create_road_marking),
        (RoadMarkingReal, "roadmarkingreal", get_data_create_road_marking),
        (SignpostPlan, "signpostplan", get_data_create_signpost),
        (SignpostReal, "signpostreal", get_data_create_signpost),
        (TrafficLightPlan, "trafficlightplan", get_data_create_traffic_light),
        (TrafficLightReal, "trafficlightreal", get_data_create_traffic_light),
        (TrafficSignPlan, "trafficsignplan", get_data_create_traffic_sign),
        (TrafficSignReal, "trafficsignreal", get_data_create_traffic_sign),
    ),
)
@pytest.mark.django_db
def test__traffic_sign__source_name_source_id(model, url_name, data_factory):
    """Test that source_name and source_id are unique in non-deleted objects."""

    client = get_api_client(user=get_user(admin=True))
    data = data_factory()
    data.update(
        {
            "source_name": "sourcename",
            "source_id": "1",
        }
    )

    # First object OK
    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.content
    response_json = response.json()
    assert response_json["source_name"] == "sourcename"
    assert response_json["source_id"] == "1"
    assert model.objects.count() == 1
    assert model.objects.first().source_name == "sourcename"
    assert model.objects.first().source_id == "1"
    first_id = response_json["id"]

    # Second object with same source_name and source_id should fail
    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert model.objects.count() == 1

    # Delete the object
    response = client.delete(reverse(f"v1:{url_name}-detail", kwargs={"pk": first_id}))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert model.objects.count() == 1
    assert model.objects.first().is_active is False

    # This time addition should be OK since the object is soft-deleted
    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["source_name"] == "sourcename"
    assert response_json["source_id"] == "1"
    assert model.objects.count() == 2
    newer_object = model.objects.get(is_active=True)
    assert newer_object.source_name == "sourcename"
    assert newer_object.source_id == "1"
