import json

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from traffic_control import models
from traffic_control.models import BarrierPlan, Lifecycle
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_operational_area,
    get_owner,
    get_plan,
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

test_point_inside_area = Point(20.0, 20.0, srid=settings.SRID)
test_point_outside_area = Point(-20.0, -20.0, srid=settings.SRID)
test_3d_point_inside_area = Point(20.0, 20.0, 0.0, srid=settings.SRID)
test_3d_point_outside_area = Point(-20.0, -20.0, 0.0, srid=settings.SRID)
test_multipolygon_inside_area = MultiPolygon(
    Polygon(
        ((20.0, 20.0), (20.0, 30.0), (30.0, 30.0), (30.0, 20.0), (20.0, 20.0)),
        srid=settings.SRID,
    ),
    srid=settings.SRID,
)
test_multipolygon_outside_area = MultiPolygon(
    Polygon(
        (
            (-20.0, -20.0),
            (-20.0, -30.0),
            (-30.0, -30.0),
            (-30.0, -20.0),
            (-20.0, -20.0),
        ),
        srid=settings.SRID,
    ),
    srid=settings.SRID,
)

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
    "model,location,success",
    (
        ("AdditionalSignPlan", test_3d_point_inside_area, True),
        ("AdditionalSignPlan", test_3d_point_outside_area, False),
        ("AdditionalSignPlan", None, False),
        ("AdditionalSignReal", test_3d_point_inside_area, True),
        ("AdditionalSignReal", test_3d_point_outside_area, False),
        ("AdditionalSignReal", None, False),
        ("BarrierPlan", test_point_inside_area, True),
        ("BarrierPlan", test_point_outside_area, False),
        ("BarrierPlan", None, False),
        ("BarrierReal", test_point_inside_area, True),
        ("BarrierReal", test_point_outside_area, False),
        ("BarrierReal", None, False),
        ("MountPlan", test_point_inside_area, True),
        ("MountPlan", test_point_outside_area, False),
        ("MountPlan", None, False),
        ("MountReal", test_point_inside_area, True),
        ("MountReal", test_point_outside_area, False),
        ("MountReal", None, False),
        ("Plan", test_multipolygon_inside_area, True),
        ("Plan", test_multipolygon_outside_area, False),
        ("Plan", None, True),
        ("RoadMarkingPlan", test_point_inside_area, True),
        ("RoadMarkingPlan", test_point_outside_area, False),
        ("RoadMarkingPlan", None, False),
        ("RoadMarkingReal", test_point_inside_area, True),
        ("RoadMarkingReal", test_point_outside_area, False),
        ("RoadMarkingReal", None, False),
        ("SignpostPlan", test_point_inside_area, True),
        ("SignpostPlan", test_point_outside_area, False),
        ("SignpostPlan", None, False),
        ("SignpostReal", test_point_inside_area, True),
        ("SignpostReal", test_point_outside_area, False),
        ("SignpostReal", None, False),
        ("TrafficLightPlan", test_point_inside_area, True),
        ("TrafficLightPlan", test_point_outside_area, False),
        ("TrafficLightPlan", None, False),
        ("TrafficLightReal", test_point_inside_area, True),
        ("TrafficLightReal", test_point_outside_area, False),
        ("TrafficLightReal", None, False),
        ("TrafficSignPlan", test_3d_point_inside_area, True),
        ("TrafficSignPlan", test_3d_point_outside_area, False),
        ("TrafficSignPlan", None, False),
        ("TrafficSignReal", test_3d_point_inside_area, True),
        ("TrafficSignReal", test_3d_point_outside_area, False),
        ("TrafficSignReal", None, False),
    ),
)
def test__api_operational_area_permission__create(model, location, success):
    operational_area = get_operational_area()
    user = get_user()
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.operational_areas.add(operational_area)
    user.user_permissions.add(*perms)
    device_type = get_traffic_control_device_type()

    location = location.ewkt if location else None

    if model == "Plan":
        data = {
            "name": "Test plan",
            "plan_number": "2020_1",
            "location": location,
            "planner": user.pk,
            "decision_maker": user.pk,
            "linked_objects": {
                "barrier_plan_ids": [],
                "mount_plan_ids": [],
                "road_marking_plan_ids": [],
                "signpost_plan_ids": [],
                "traffic_light_plan_ids": [],
                "traffic_sign_plan_ids": [],
                "additional_sign_plan_ids": [],
            },
        }
    else:
        data = {
            "location": location,
            "device_type": device_type.pk,
            "decision_date": "2020-07-01",
            "lifecycle": Lifecycle.ACTIVE.value,
            "owner": get_owner().pk,
        }

        if model in ["BarrierPlan", "BarrierReal"]:
            data["road_name"] = "testroad"
        elif model in ["RoadMarkingPlan", "RoadMarkingReal"]:
            data["source_id"] = 1
            data["source_name"] = "test source"

    api_client = get_api_client(user=user)
    response = api_client.post(
        reverse(f"v1:{model.lower()}-list"), data=data, format="json"
    )

    ModelClass = getattr(models, model)  # noqa: N806
    if success:
        assert response.status_code == status.HTTP_201_CREATED
        assert ModelClass.objects.count() == 1
    elif not location:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"location": [_("This field may not be null.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert ModelClass.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "location,success",
    ((test_point_inside_area, True), (test_point_outside_area, False), (None, False)),
)
def test__api_operational_area_permission__create__geojson(location, success):
    operational_area = get_operational_area()
    user = get_user()
    perms = Permission.objects.filter(codename__contains="barrierplan")
    user.operational_areas.add(operational_area)
    user.user_permissions.add(*perms)
    device_type = get_traffic_control_device_type()

    if location:
        location = json.loads(location.geojson)
        location.update(
            {"crs": {"type": "name", "properties": {"name": f"EPSG:{settings.SRID}"}}}
        )

    data = {
        "location": location,
        "device_type": device_type.pk,
        "decision_date": "2020-07-01",
        "lifecycle": Lifecycle.ACTIVE.value,
        "owner": get_owner().pk,
        "road_name": "testroad",
    }

    api_client = get_api_client(user=user)
    response = api_client.post(
        f"{reverse('v1:barrierplan-list')}?geo_format=geojson", data=data, format="json"
    )

    if success:
        assert response.status_code == status.HTTP_201_CREATED
        assert BarrierPlan.objects.count() == 1
    elif not location:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"location": [_("This field may not be null.")]}
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert BarrierPlan.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,location,success",
    (
        ("AdditionalSignPlan", test_3d_point_inside_area, True),
        ("AdditionalSignPlan", test_3d_point_outside_area, False),
        ("AdditionalSignReal", test_3d_point_inside_area, True),
        ("AdditionalSignReal", test_3d_point_outside_area, False),
        ("BarrierPlan", test_point_inside_area, True),
        ("BarrierPlan", test_point_outside_area, False),
        ("BarrierReal", test_point_inside_area, True),
        ("BarrierReal", test_point_outside_area, False),
        ("MountPlan", test_point_inside_area, True),
        ("MountPlan", test_point_outside_area, False),
        ("MountReal", test_point_inside_area, True),
        ("MountReal", test_point_outside_area, False),
        ("Plan", test_multipolygon_inside_area, True),
        ("Plan", test_multipolygon_outside_area, False),
        ("RoadMarkingPlan", test_point_inside_area, True),
        ("RoadMarkingPlan", test_point_outside_area, False),
        ("RoadMarkingReal", test_point_inside_area, True),
        ("RoadMarkingReal", test_point_outside_area, False),
        ("SignpostPlan", test_point_inside_area, True),
        ("SignpostPlan", test_point_outside_area, False),
        ("SignpostReal", test_point_inside_area, True),
        ("SignpostReal", test_point_outside_area, False),
        ("TrafficLightPlan", test_point_inside_area, True),
        ("TrafficLightPlan", test_point_outside_area, False),
        ("TrafficLightReal", test_point_inside_area, True),
        ("TrafficLightReal", test_point_outside_area, False),
        ("TrafficSignPlan", test_3d_point_inside_area, True),
        ("TrafficSignPlan", test_3d_point_outside_area, False),
        ("TrafficSignReal", test_3d_point_inside_area, True),
        ("TrafficSignReal", test_3d_point_outside_area, False),
    ),
)
def test__api_operational_area_permission__update(model, location, success):
    operational_area = get_operational_area()
    user = get_user()
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.operational_areas.add(operational_area)
    user.user_permissions.add(*perms)
    device_type = get_traffic_control_device_type()
    instance = model_factory_map[model](location=location)

    if model == "Plan":
        data = {
            "name": "Test plan",
            "plan_number": "2020_1",
            "location": location.ewkt,
            "planner": user.pk,
            "decision_maker": user.pk,
            "linked_objects": {
                "barrier_plan_ids": [],
                "mount_plan_ids": [],
                "road_marking_plan_ids": [],
                "signpost_plan_ids": [],
                "traffic_light_plan_ids": [],
                "traffic_sign_plan_ids": [],
                "additional_sign_plan_ids": [],
            },
        }
    else:
        data = {
            "location": location.ewkt,
            "device_type": device_type.pk,
            "decision_date": "2020-07-01",
            "lifecycle": Lifecycle.ACTIVE.value,
            "owner": get_owner().pk,
        }

        if model in ["BarrierPlan", "BarrierReal"]:
            data["road_name"] = "testroad"
        elif model in ["RoadMarkingPlan", "RoadMarkingReal"]:
            data["source_id"] = 1
            data["source_name"] = "test source"

    api_client = get_api_client(user=user)
    response = api_client.put(
        reverse(f"v1:{model.lower()}-detail", kwargs={"pk": instance.pk}),
        data,
        format="json",
    )

    instance.refresh_from_db()
    if success:
        assert response.status_code == status.HTTP_200_OK
        assert instance.updated_by == user
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert instance.updated_by != user


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,location,success",
    (
        ("AdditionalSignPlan", test_3d_point_inside_area, True),
        ("AdditionalSignPlan", test_3d_point_outside_area, False),
        ("AdditionalSignReal", test_3d_point_inside_area, True),
        ("AdditionalSignReal", test_3d_point_outside_area, False),
        ("BarrierPlan", test_point_inside_area, True),
        ("BarrierPlan", test_point_outside_area, False),
        ("BarrierReal", test_point_inside_area, True),
        ("BarrierReal", test_point_outside_area, False),
        ("MountPlan", test_point_inside_area, True),
        ("MountPlan", test_point_outside_area, False),
        ("MountReal", test_point_inside_area, True),
        ("MountReal", test_point_outside_area, False),
        ("Plan", test_multipolygon_inside_area, True),
        ("Plan", test_multipolygon_outside_area, False),
        ("RoadMarkingPlan", test_point_inside_area, True),
        ("RoadMarkingPlan", test_point_outside_area, False),
        ("RoadMarkingReal", test_point_inside_area, True),
        ("RoadMarkingReal", test_point_outside_area, False),
        ("SignpostPlan", test_point_inside_area, True),
        ("SignpostPlan", test_point_outside_area, False),
        ("SignpostReal", test_point_inside_area, True),
        ("SignpostReal", test_point_outside_area, False),
        ("TrafficLightPlan", test_point_inside_area, True),
        ("TrafficLightPlan", test_point_outside_area, False),
        ("TrafficLightReal", test_point_inside_area, True),
        ("TrafficLightReal", test_point_outside_area, False),
        ("TrafficSignPlan", test_3d_point_inside_area, True),
        ("TrafficSignPlan", test_3d_point_outside_area, False),
        ("TrafficSignReal", test_3d_point_inside_area, True),
        ("TrafficSignReal", test_3d_point_outside_area, False),
    ),
)
def test__api_operational_area_permission__partial_update(model, location, success):
    operational_area = get_operational_area()
    user = get_user()
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.operational_areas.add(operational_area)
    user.user_permissions.add(*perms)
    instance = model_factory_map[model](location=location)

    data = {
        "location": location.ewkt,
    }
    api_client = get_api_client(user=user)
    response = api_client.patch(
        reverse(f"v1:{model.lower()}-detail", kwargs={"pk": instance.pk}),
        data,
        format="json",
    )

    instance.refresh_from_db()
    if success:
        assert response.status_code == status.HTTP_200_OK
        assert instance.updated_by == user
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert instance.updated_by != user


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,location,success",
    (
        ("AdditionalSignPlan", test_3d_point_inside_area, True),
        ("AdditionalSignPlan", test_3d_point_outside_area, False),
        ("AdditionalSignReal", test_3d_point_inside_area, True),
        ("AdditionalSignReal", test_3d_point_outside_area, False),
        ("BarrierPlan", test_point_inside_area, True),
        ("BarrierPlan", test_point_outside_area, False),
        ("BarrierReal", test_point_inside_area, True),
        ("BarrierReal", test_point_outside_area, False),
        ("MountPlan", test_point_inside_area, True),
        ("MountPlan", test_point_outside_area, False),
        ("MountReal", test_point_inside_area, True),
        ("MountReal", test_point_outside_area, False),
        ("Plan", test_multipolygon_inside_area, True),
        ("Plan", test_multipolygon_outside_area, False),
        ("RoadMarkingPlan", test_point_inside_area, True),
        ("RoadMarkingPlan", test_point_outside_area, False),
        ("RoadMarkingReal", test_point_inside_area, True),
        ("RoadMarkingReal", test_point_outside_area, False),
        ("SignpostPlan", test_point_inside_area, True),
        ("SignpostPlan", test_point_outside_area, False),
        ("SignpostReal", test_point_inside_area, True),
        ("SignpostReal", test_point_outside_area, False),
        ("TrafficLightPlan", test_point_inside_area, True),
        ("TrafficLightPlan", test_point_outside_area, False),
        ("TrafficLightReal", test_point_inside_area, True),
        ("TrafficLightReal", test_point_outside_area, False),
        ("TrafficSignPlan", test_3d_point_inside_area, True),
        ("TrafficSignPlan", test_3d_point_outside_area, False),
        ("TrafficSignReal", test_3d_point_inside_area, True),
        ("TrafficSignReal", test_3d_point_outside_area, False),
    ),
)
def test__api_operational_area_permission__delete(model, location, success):
    operational_area = get_operational_area()
    user = get_user()
    perms = Permission.objects.filter(codename__contains=model.lower())
    user.operational_areas.add(operational_area)
    user.user_permissions.add(*perms)
    instance = model_factory_map[model](location=location)

    api_client = get_api_client(user=user)
    response = api_client.delete(
        reverse(f"v1:{model.lower()}-detail", kwargs={"pk": instance.pk})
    )

    instance.refresh_from_db()
    if success:
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not instance.is_active
    else:
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert instance.is_active
