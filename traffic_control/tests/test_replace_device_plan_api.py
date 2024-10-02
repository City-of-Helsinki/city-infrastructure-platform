from uuid import UUID, uuid4

import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.models import (
    AdditionalSignPlan,
    BarrierPlan,
    MountPlan,
    RoadMarkingPlan,
    SignpostPlan,
    TrafficLightPlan,
    TrafficSignPlan,
)
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_api_client,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_owner,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    get_user,
)
from traffic_control.tests.test_base_api_3d import test_point_2_3d, test_point_3_3d, test_point_3d, test_point_5_3d

model_factory_url_name = (
    (TrafficSignPlan, get_traffic_sign_plan, "trafficsignplan"),
    (AdditionalSignPlan, get_additional_sign_plan, "additionalsignplan"),
    (MountPlan, get_mount_plan, "mountplan"),
    (TrafficLightPlan, get_traffic_light_plan, "trafficlightplan"),
    (SignpostPlan, get_signpost_plan, "signpostplan"),
    (BarrierPlan, get_barrier_plan, "barrierplan"),
    (RoadMarkingPlan, get_road_marking_plan, "roadmarkingplan"),
)


plan_factory_url_name_plan_relation_name_real_factory = (
    (get_traffic_sign_plan, "trafficsignplan", "traffic_sign_plan", get_traffic_sign_real),
    (get_mount_plan, "mountplan", "mount_plan", get_mount_real),
    (get_additional_sign_plan, "additionalsignplan", "additional_sign_plan", get_additional_sign_real),
    (get_traffic_light_plan, "trafficlightplan", "traffic_light_plan", get_traffic_light_real),
    (get_signpost_plan, "signpostplan", "signpost_plan", get_signpost_real),
    (get_barrier_plan, "barrierplan", "barrier_plan", get_barrier_real),
    (get_road_marking_plan, "roadmarkingplan", "road_marking_plan", get_road_marking_real),
)


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__default_list_only_unreplaced_devices(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    replaced_device_1 = factory(location=test_point_3d)
    replaced_device_2 = factory(location=test_point_2_3d, replaces=replaced_device_1)
    unreplaced_device_1 = factory(location=test_point_3_3d, replaces=replaced_device_2)
    unreplaced_device_2 = factory(location=test_point_5_3d)

    response = client.get(reverse(f"v1:{url_name}-list"), format="json")

    assert model.objects.count() == 4
    assert response.status_code == status.HTTP_200_OK, response.json()
    response_json = response.json()
    assert response_json.get("count") == 2
    result_device_ids = [UUID(result.get("id")) for result in response_json.get("results")]
    assert unreplaced_device_1.id in result_device_ids
    assert unreplaced_device_2.id in result_device_ids


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__list_only_replaced_devices(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    replaced_device_1 = factory(location=test_point_3d)
    replaced_device_2 = factory(location=test_point_2_3d, replaces=replaced_device_1)
    _ = factory(location=test_point_3_3d, replaces=replaced_device_2)
    _ = factory(location=test_point_5_3d)

    response = client.get(reverse(f"v1:{url_name}-list"), {"is_replaced": "true"}, format="json")

    assert model.objects.count() == 4
    assert response.status_code == status.HTTP_200_OK, response.json()
    response_json = response.json()
    assert response_json.get("count") == 2
    result_device_ids = [UUID(result.get("id")) for result in response_json.get("results")]
    assert replaced_device_1.id in result_device_ids
    assert replaced_device_2.id in result_device_ids


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__list_all_devices(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    replaced_device_1 = factory(location=test_point_3d)
    replaced_device_2 = factory(location=test_point_2_3d, replaces=replaced_device_1)
    unreplaced_device_1 = factory(location=test_point_3_3d, replaces=replaced_device_2)
    unreplaced_device_2 = factory(location=test_point_5_3d)

    response = client.get(reverse(f"v1:{url_name}-list"), {"is_replaced": "All"}, format="json")

    assert model.objects.count() == 4
    assert response.status_code == status.HTTP_200_OK, response.json()
    response_json = response.json()
    assert response_json.get("count") == 4
    result_device_ids = [UUID(result.get("id")) for result in response_json.get("results")]
    assert replaced_device_1.id in result_device_ids
    assert unreplaced_device_1.id in result_device_ids
    assert unreplaced_device_2.id in result_device_ids


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__detail_replaced_device(model, factory, url_name):
    """It should be possible to fetch detailed view of replaced device"""

    client = get_api_client(user=get_user(admin=True))
    replaced_device = factory(location=test_point_3d)
    unreplaced_device = factory(location=test_point_2_3d, replaces=replaced_device)
    response = client.get(reverse(f"v1:{url_name}-detail", kwargs={"pk": replaced_device.id}), format="json")
    assert response.status_code == status.HTTP_200_OK, response.json()
    response_json = response.json()
    assert response_json.get("id") == str(replaced_device.id)
    assert response_json.get("replaced_by") == str(unreplaced_device.id)
    assert response_json.get("is_replaced") is True


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__create__old_is_marked_replaced(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory()

    data = {
        "replaces": old_device.id,
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    if model == BarrierPlan:
        data["road_name"] = "Road name"

    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")
    old_device.refresh_from_db()

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert model.objects.count() == 2
    response_json = response.json()
    assert response_json.get("replaced_by") is None
    assert response_json.get("replaces") == str(old_device.id)
    assert old_device.replaced_by.id == UUID(response_json.get("id"))
    assert old_device.replaces is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__old_is_marked_replaced(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_2_3d)

    data = {
        "replaces": old_device.id,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert model.objects.count() == 2
    response_json = response.json()
    assert response_json.get("replaced_by") is None
    assert response_json.get("replaces") == str(old_device.id)
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device
    assert old_device.replaced_by == new_device
    assert old_device.replaces is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__change_replaced(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device1 = factory(location=test_point_3d)
    old_device2 = factory(location=test_point_2_3d)
    new_device = factory(location=test_point_3_3d, replaces=old_device1)

    data = {
        "replaces": old_device2.id,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")
    old_device1.refresh_from_db()
    old_device2.refresh_from_db()
    new_device.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert model.objects.count() == 3
    response_json = response.json()
    assert response_json.get("replaced_by") is None
    assert response_json.get("replaces") == str(old_device2.id)
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device2
    assert old_device1.replaced_by is None
    assert old_device1.replaces is None
    assert old_device2.replaced_by == new_device
    assert old_device2.replaces is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__remove_replacement(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_2_3d, replaces=old_device)

    data = {
        "replaces": None,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert model.objects.count() == 2
    response_json = response.json()
    assert response_json.get("replaced_by") is None
    assert response_json.get("replaces") is None
    assert new_device.replaced_by is None
    assert new_device.replaces is None
    assert old_device.replaced_by is None
    assert old_device.replaces is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__without_replacement_should_not_affect(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_2_3d, replaces=old_device)

    data = {
        # Update something else than replacements
        "location": test_point_3_3d.ewkt,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK, response.json()
    assert model.objects.count() == 2
    response_json = response.json()
    assert response_json.get("replaced_by") is None
    assert response_json.get("replaces") == str(old_device.id)
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device
    assert old_device.replaced_by == new_device
    assert old_device.replaces is None


@pytest.mark.parametrize(
    ("plan_factory", "plan_url_name", "plan_relation_name", "real_factory"),
    plan_factory_url_name_plan_relation_name_real_factory,
)
@pytest.mark.django_db
def test__device_plan_replace__create__real_devices_plan_is_updated_to_replacer(
    plan_factory,
    plan_url_name,
    plan_relation_name,
    real_factory,
):
    client = get_api_client(user=get_user(admin=True))
    old_device_plan = plan_factory()
    device_real = real_factory(**{plan_relation_name: old_device_plan})

    data = {
        "replaces": old_device_plan.id,
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    if plan_url_name == "barrierplan":
        data["road_name"] = "Road name"

    response = client.post(reverse(f"v1:{plan_url_name}-list"), data, format="json")
    old_device_plan.refresh_from_db()
    device_real.refresh_from_db()

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert getattr(device_real, plan_relation_name).id == UUID(response.json().get("id"))


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__create__cannot_replace_already_replaced(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))

    replaced_device = factory(location=test_point_2_3d)
    newer_device = factory(location=test_point_3d, replaces=replaced_device)

    data = {
        "replaces": replaced_device.id,
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")
    newer_device.refresh_from_db()
    replaced_device.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert replaced_device.replaced_by == newer_device
    assert newer_device.replaced_by is None
    assert model.objects.count() == 2


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__cannot_replace_self__patch(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    device = factory()

    data = {
        "replaces": device.id,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": device.id}), data, format="json")
    device.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert device.replaces is None
    assert device.replaced_by is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__cannot_replace_self__put(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    device = factory()

    data = {
        "replaces": device.id,
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    response = client.put(reverse(f"v1:{url_name}-detail", kwargs={"pk": device.id}), data, format="json")
    device.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert device.replaces is None
    assert device.replaced_by is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__cannot_make_circular_replacement__patch(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))

    device_1 = factory(location=test_point_3d)
    device_2 = factory(location=test_point_2_3d, replaces=device_1)
    device_3 = factory(location=test_point_3_3d, replaces=device_2)

    data = {
        "replaces": device_3.id,
    }
    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": device_1.id}), data, format="json")
    device_1.refresh_from_db()
    device_2.refresh_from_db()
    device_3.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert device_1.replaced_by == device_2
    assert device_2.replaced_by == device_3
    assert device_3.replaced_by is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__cannot_make_circular_replacement__put(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))

    device_1 = factory(location=test_point_3d)
    device_2 = factory(location=test_point_2_3d, replaces=device_1)
    device_3 = factory(location=test_point_3_3d, replaces=device_2)

    data = {
        "replaces": device_3.id,
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    response = client.put(reverse(f"v1:{url_name}-detail", kwargs={"pk": device_1.id}), data, format="json")
    device_1.refresh_from_db()
    device_2.refresh_from_db()
    device_3.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert device_1.replaced_by == device_2
    assert device_2.replaced_by == device_3
    assert device_3.replaced_by is None


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__create__replaces_not_found(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))

    data = {
        "replaces": uuid4(),
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    if model == BarrierPlan:
        data["road_name"] = "Road name"

    response = client.post(reverse(f"v1:{url_name}-list"), data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert response.json().get("replaces") == ["The device plan to be replaced does not exist"]


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__replaces_not_found__patch(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_3_3d, replaces=old_device)

    data = {
        "replaces": uuid4(),
    }

    response = client.patch(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert response.json().get("replaces") == ["The device plan to be replaced does not exist"]


@pytest.mark.parametrize(("model", "factory", "url_name"), model_factory_url_name)
@pytest.mark.django_db
def test__device_plan_replace__update__replaces_not_found__put(model, factory, url_name):
    client = get_api_client(user=get_user(admin=True))
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_3_3d, replaces=old_device)

    data = {
        "replaces": uuid4(),
        "location": test_point_3d.ewkt,
        "owner": get_owner().id,
    }
    if model == BarrierPlan:
        data["road_name"] = "Road name"

    response = client.put(reverse(f"v1:{url_name}-detail", kwargs={"pk": new_device.id}), data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.json()
    assert response.json().get("replaces") == ["The device plan to be replaced does not exist"]


@pytest.mark.parametrize("has_previous_plan", (True, False), ids=("has_previous_plan", "no_previous_plan"))
@pytest.mark.parametrize("has_real_device", (True, False), ids=("has_real_device", "no_real_device"))
@pytest.mark.parametrize(
    ("plan_factory", "plan_url_name", "plan_relation_name", "real_factory"),
    plan_factory_url_name_plan_relation_name_real_factory,
)
@pytest.mark.django_db
def test__device_plan_replace__delete(
    plan_factory,
    plan_url_name,
    plan_relation_name,
    real_factory,
    has_previous_plan,
    has_real_device,
):
    """
    Deleting a device plan makes its real device (if any) move it back to the previous plan (if any).
    """
    client = get_api_client(user=get_user(admin=True))

    previous_device_plan = plan_factory(location=test_point_3d) if has_previous_plan else None
    current_device_plan = plan_factory(location=test_point_2_3d, replaces=previous_device_plan)

    if has_real_device:
        device_real = real_factory(location=test_point_3_3d, **{plan_relation_name: current_device_plan})

    response = client.delete(
        reverse(f"v1:{plan_url_name}-detail", kwargs={"pk": current_device_plan.id}), format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    if has_previous_plan:
        previous_device_plan.refresh_from_db()
        assert previous_device_plan.replaced_by is None

    if has_real_device:
        device_real.refresh_from_db()
        if has_previous_plan:
            assert getattr(device_real, plan_relation_name) == previous_device_plan
        else:
            assert getattr(device_real, plan_relation_name) is None
