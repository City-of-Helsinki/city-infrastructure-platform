import pytest
from django.core.exceptions import ValidationError

from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal
from city_furniture.resources import FurnitureSignpostPlanResource, FurnitureSignpostRealResource
from city_furniture.tests.factories import get_furniture_signpost_plan, get_furniture_signpost_real
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    BarrierPlan,
    BarrierReal,
    MountPlan,
    MountReal,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.resources import (
    AdditionalSignPlanResource,
    AdditionalSignRealResource,
    BarrierPlanResource,
    BarrierRealResource,
    MountPlanResource,
    MountRealResource,
    RoadMarkingPlanResource,
    RoadMarkingRealResource,
    SignpostPlanResource,
    SignpostRealResource,
    TrafficLightPlanResource,
    TrafficLightRealResource,
    TrafficSignPlanResource,
    TrafficSignRealResource,
)
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_additional_sign_plan,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_responsible_entity_project,
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
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset

_models_resources_factories = (
    (FurnitureSignpostPlan, FurnitureSignpostPlanResource, get_furniture_signpost_plan),
    (FurnitureSignpostReal, FurnitureSignpostRealResource, get_furniture_signpost_real),
    (AdditionalSignPlan, AdditionalSignPlanResource, get_additional_sign_plan),
    (AdditionalSignReal, AdditionalSignRealResource, AdditionalSignRealFactory),
    (BarrierPlan, BarrierPlanResource, get_barrier_plan),
    (BarrierReal, BarrierRealResource, get_barrier_real),
    (MountPlan, MountPlanResource, get_mount_plan),
    (MountReal, MountRealResource, get_mount_real),
    (RoadMarkingPlan, RoadMarkingPlanResource, get_road_marking_plan),
    (RoadMarkingReal, RoadMarkingRealResource, get_road_marking_real),
    (SignpostPlan, SignpostPlanResource, get_signpost_plan),
    (SignpostReal, SignpostRealResource, get_signpost_real),
    (TrafficLightPlan, TrafficLightPlanResource, get_traffic_light_plan),
    (TrafficLightReal, TrafficLightRealResource, get_traffic_light_real),
    (TrafficSignPlan, TrafficSignPlanResource, get_traffic_sign_plan),
    (TrafficSignReal, TrafficSignRealResource, get_traffic_sign_real),
)


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_import_without_re(
    model,
    resource,
    factory,
    format,
):
    """User cannot import a new device because they don't belong to the responsible entity"""
    re_project = get_responsible_entity_project()

    factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    user = get_user()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.all().count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_can_import_to_their_re(
    model,
    resource,
    factory,
    format,
):
    """User can import a new device because they belong to the same responsible entity"""
    re_project = get_responsible_entity_project()

    user = get_user()
    user.responsible_entities.add(re_project)

    factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.first().responsible_entity == re_project


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_can_import_to_child_re(
    model,
    resource,
    factory,
    format,
):
    """User can import a new device because they belong to a higher level responsible entity"""
    re_project = get_responsible_entity_project()
    re_parent = re_project.parent
    assert re_parent is not None

    user = get_user()
    user.responsible_entities.add(re_parent)

    factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    result = resource().import_data(dataset, raise_errors=True, user=user)
    assert not result.has_errors()
    assert model.objects.all().count() == 1
    assert model.objects.first().responsible_entity == re_project


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_import_new_devices_to_another_re(
    model,
    resource,
    factory,
    format,
):
    """User cannot import a new device of another responsible entity"""
    re_project = get_responsible_entity_project()
    another_re_project = get_responsible_entity_project(name="Another project")

    user = get_user()
    user.responsible_entities.add(re_project)

    factory(responsible_entity=another_re_project)
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    model.objects.all().delete()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.all().count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_move_device_from_another_re_to_theirs(
    model,
    resource,
    factory,
    format,
):
    """User cannot move a device from another responsible entity to theirs using import"""
    re_project = get_responsible_entity_project()
    another_re_project = get_responsible_entity_project(name="Another project")

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = another_re_project
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=re_project).count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_move_device_from_non_re_to_theirs(
    model,
    resource,
    factory,
    format,
):
    """User cannot move a device from non-responsible entity to theirs using import"""
    re_project = get_responsible_entity_project()

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = None
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=re_project).count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_move_device_from_non_re_to_non_theirs(
    model,
    resource,
    factory,
    format,
):
    """User cannot move a device from non-responsible entity to another using import"""
    re_project = get_responsible_entity_project()
    another_re_project = get_responsible_entity_project(name="Another project")

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=another_re_project)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = None
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=another_re_project).count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_remove_device_from_their_re(
    model,
    resource,
    factory,
    format,
):
    """User cannot remove a device from their responsible entity using import"""
    re_project = get_responsible_entity_project()

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=None)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = re_project
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=re_project).count() == 1


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_remove_device_from_another_re(
    model,
    resource,
    factory,
    format,
):
    """User cannot remove a device from a responsible entity that they don't belong in using import"""
    re_project = get_responsible_entity_project()
    another_re_project = get_responsible_entity_project(name="Another project")

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=None)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = another_re_project
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=another_re_project).count() == 1


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_cannot_move_device_to_their_parent_re(
    model,
    resource,
    factory,
    format,
):
    """User cannot move a device from their responsible entity their parent responsible entity using import"""
    re_project = get_responsible_entity_project()
    re_parent = re_project.parent
    assert re_parent is not None

    user = get_user()
    user.responsible_entities.add(re_project)

    device = factory(responsible_entity=re_parent)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = re_project
    device.save()

    with pytest.raises(ValidationError):
        resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.filter(responsible_entity=re_parent).count() == 0


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_can_move_device_from_child_re_to_another(
    model,
    resource,
    factory,
    format,
):
    """User can move a device from their child responsible entity to another child using import"""
    re_project_1 = get_responsible_entity_project(name="Project 1")
    re_project_2 = get_responsible_entity_project(name="Project 2")
    re_parent = re_project_1.parent
    assert re_parent is not None
    assert re_parent == re_project_2.parent

    user = get_user()
    user.responsible_entities.add(re_parent)

    device = factory(responsible_entity=re_project_2)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = re_project_1
    device.save()

    resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.get(id=device.id).responsible_entity == re_project_2


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_can_move_device_from_child_to_theirs(
    model,
    resource,
    factory,
    format,
):
    """User can move a device from their child responsible entity to their responsible entity using import"""
    re_project = get_responsible_entity_project()
    re_parent = re_project.parent
    assert re_parent is not None

    user = get_user()
    user.responsible_entities.add(re_parent)

    device = factory(responsible_entity=re_parent)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = re_project
    device.save()

    resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.get(id=device.id).responsible_entity == re_parent


@pytest.mark.parametrize(("model", "resource", "factory"), _models_resources_factories)
@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__import__device__responsible_entity__user_can_move_device_from_theirs_to_child(
    model,
    resource,
    factory,
    format,
):
    """User can move a device from their responsible entity to a child using import"""
    re_project = get_responsible_entity_project()
    re_parent = re_project.parent
    assert re_parent is not None

    user = get_user()
    user.responsible_entities.add(re_parent)

    device = factory(responsible_entity=re_project)
    dataset = get_import_dataset(resource, format=format)
    device.responsible_entity = re_parent
    device.save()

    resource().import_data(dataset, raise_errors=True, user=user)
    assert model.objects.get(id=device.id).responsible_entity == re_project
