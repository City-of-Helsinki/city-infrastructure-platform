import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status

from traffic_control import models
from traffic_control.enums import Lifecycle
from traffic_control.tests.factories import (
    get_api_client,
    get_owner,
    get_responsible_entity_project,
    get_user,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)
from traffic_control.tests.test_base_api_3d import test_point_3d


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model",
    (
        "AdditionalSignPlan",
        "AdditionalSignReal",
        "BarrierPlan",
        "BarrierReal",
        "MountPlan",
        "MountReal",
        "RoadMarkingPlan",
        "RoadMarkingReal",
        "SignpostPlan",
        "SignpostReal",
        "TrafficLightPlan",
        "TrafficLightReal",
        "TrafficSignPlan",
        "TrafficSignReal",
    ),
)
@pytest.mark.parametrize(
    "add_to_responsible_entity",
    (True, False),
    ids=lambda added: "added" if added else "not_added",
)
def test__api_responsible_area_permission__create(model, add_to_responsible_entity):
    user = get_user(bypass_operational_area=True)
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.user_permissions.add(*perms)
    responsible_entity = get_responsible_entity_project()

    data = {
        "location": str(test_point_3d),
        "device_type": TrafficControlDeviceTypeFactory().pk,
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": get_owner().pk,
        "responsible_entity": responsible_entity.pk,
    }

    if model in ["BarrierPlan", "BarrierReal"]:
        data["road_name"] = "testroad"
    elif model == "AdditionalSignReal":
        data["parent"] = TrafficSignRealFactory().pk
    elif model == "AdditionalSignPlan":
        data["parent"] = TrafficSignPlanFactory().pk

    client = get_api_client(user=user)
    model_class = getattr(models, model)

    if add_to_responsible_entity:
        user.responsible_entities.add(responsible_entity)
        response = client.post(reverse(f"v1:{model.lower()}-list"), data=data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert model_class.objects.count() == 1
    else:
        response = client.post(reverse(f"v1:{model.lower()}-list"), data=data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert model_class.objects.count() == 0
