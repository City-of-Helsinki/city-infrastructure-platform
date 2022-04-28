import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status

from traffic_control import models
from traffic_control.enums import Lifecycle
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_owner,
    get_plan,
    get_responsible_entity,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_control_device_type,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)
from traffic_control.tests.test_base_api_3d import test_point_3d

model_factory_map = {
    "AdditionalSignPlan": get_additional_sign_plan,
    "AdditionalSignReal": get_additional_sign_real,
    "BarrierPlan": get_barrier_plan,
    "BarrierReal": get_barrier_real,
    "MountPlan": get_mount_plan,
    "MountReal": get_mount_real,
    "Plan": get_plan,
    "RoadMarkingPlan": get_road_marking_plan,
    "RoadMarkingReal": get_road_marking_real,
    "SignpostPlan": get_signpost_plan,
    "SignpostReal": get_signpost_real,
    "TrafficLightPlan": get_traffic_light_plan,
    "TrafficLightReal": get_traffic_light_real,
    "TrafficSignPlan": get_traffic_sign_plan,
    "TrafficSignReal": get_traffic_sign_real,
}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model, add_to_responsible_entity",
    (
        ("AdditionalSignPlan", True),
        ("AdditionalSignPlan", False),
        ("AdditionalSignReal", True),
        ("AdditionalSignReal", False),
        ("BarrierPlan", True),
        ("BarrierPlan", False),
        ("BarrierReal", True),
        ("BarrierReal", False),
        ("MountPlan", True),
        ("MountPlan", False),
        ("MountReal", True),
        ("MountReal", False),
        ("RoadMarkingPlan", True),
        ("RoadMarkingPlan", False),
        ("RoadMarkingReal", True),
        ("RoadMarkingReal", False),
        ("SignpostPlan", True),
        ("SignpostPlan", False),
        ("SignpostReal", True),
        ("SignpostReal", False),
        ("TrafficLightPlan", True),
        ("TrafficLightPlan", False),
        ("TrafficLightReal", True),
        ("TrafficLightReal", False),
        ("TrafficSignPlan", True),
        ("TrafficSignPlan", False),
        ("TrafficSignReal", True),
        ("TrafficSignReal", False),
    ),
)
def test__api_responsible_area_permission__create(model, add_to_responsible_entity):
    user = get_user(bypass_operational_area=True)
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.user_permissions.add(*perms)
    responsible_entity = get_responsible_entity()

    data = {
        "location": str(test_point_3d),
        "device_type": get_traffic_control_device_type().pk,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": get_owner().pk,
        "responsible_entity": responsible_entity.pk,
    }

    if model in ["BarrierPlan", "BarrierReal"]:
        data["road_name"] = "testroad"

    client = get_api_client(user=user)
    ModelClass = getattr(models, model)  # noqa: N806

    if add_to_responsible_entity:
        user.responsible_entities.add(responsible_entity)
        response = client.post(reverse(f"v1:{model.lower()}-list"), data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert ModelClass.objects.count() == 1
    else:
        response = client.post(reverse(f"v1:{model.lower()}-list"), data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ModelClass.objects.count() == 0
