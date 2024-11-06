import pytest

from traffic_control.models import (
    AdditionalSignPlan,
    BarrierPlan,
    MountPlan,
    RoadMarkingPlan,
    SignpostPlan,
    TrafficLightPlan,
    TrafficSignPlan,
)
from traffic_control.resources import (
    AdditionalSignPlanResource,
    BarrierPlanResource,
    MountPlanResource,
    RoadMarkingPlanResource,
    SignpostPlanResource,
    TrafficLightPlanResource,
    TrafficSignPlanResource,
)
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    get_additional_sign_plan,
    get_barrier_plan,
    get_barrier_real,
    get_mount_plan,
    get_mount_real,
    get_road_marking_plan,
    get_road_marking_real,
    get_signpost_plan,
    get_signpost_real,
    get_traffic_light_plan,
    get_traffic_light_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
)
from traffic_control.tests.test_base_api_3d import test_point_2_3d, test_point_3_3d, test_point_3d, test_point_5_3d
from traffic_control.tests.test_import_export.utils import file_formats, get_import_dataset

model_factory_resource = (
    (TrafficSignPlan, get_traffic_sign_plan, TrafficSignPlanResource),
    (AdditionalSignPlan, get_additional_sign_plan, AdditionalSignPlanResource),
    (MountPlan, get_mount_plan, MountPlanResource),
    (TrafficLightPlan, get_traffic_light_plan, TrafficLightPlanResource),
    (SignpostPlan, get_signpost_plan, SignpostPlanResource),
    (BarrierPlan, get_barrier_plan, BarrierPlanResource),
    (RoadMarkingPlan, get_road_marking_plan, RoadMarkingPlanResource),
)

plan_model_plan_factory_plan_relation_name_real_factory_resource = (
    (
        TrafficSignPlan,
        get_traffic_sign_plan,
        "traffic_sign_plan",
        get_traffic_sign_real,
        TrafficSignPlanResource,
    ),
    (
        AdditionalSignPlan,
        get_additional_sign_plan,
        "additional_sign_plan",
        AdditionalSignRealFactory,
        AdditionalSignPlanResource,
    ),
    (
        MountPlan,
        get_mount_plan,
        "mount_plan",
        get_mount_real,
        MountPlanResource,
    ),
    (
        TrafficLightPlan,
        get_traffic_light_plan,
        "traffic_light_plan",
        get_traffic_light_real,
        TrafficLightPlanResource,
    ),
    (
        SignpostPlan,
        get_signpost_plan,
        "signpost_plan",
        get_signpost_real,
        SignpostPlanResource,
    ),
    (
        BarrierPlan,
        get_barrier_plan,
        "barrier_plan",
        get_barrier_real,
        BarrierPlanResource,
    ),
    (
        RoadMarkingPlan,
        get_road_marking_plan,
        "road_marking_plan",
        get_road_marking_real,
        RoadMarkingPlanResource,
    ),
)


@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_export__list_replaced_devices(model, factory, resource):
    replaced_device_1 = factory(location=test_point_3d)
    replaced_device_2 = factory(location=test_point_2_3d, replaces=replaced_device_1)
    unreplaced_device_1 = factory(location=test_point_3_3d, replaces=replaced_device_2)
    unreplaced_device_2 = factory(location=test_point_5_3d)

    dataset = resource().export(queryset=model.objects.all().order_by("created_at"))

    assert model.objects.count() == 4
    assert len(dataset) == 4

    assert dataset.dict[0]["id"] == str(replaced_device_1.id)
    assert dataset.dict[0]["replaces"] == ""
    assert dataset.dict[0]["replaced_by"] == str(replaced_device_2.id)

    assert dataset.dict[1]["id"] == str(replaced_device_2.id)
    assert dataset.dict[1]["replaces"] == str(replaced_device_1.id)
    assert dataset.dict[1]["replaced_by"] == str(unreplaced_device_1.id)

    assert dataset.dict[2]["id"] == str(unreplaced_device_1.id)
    assert dataset.dict[2]["replaces"] == str(replaced_device_2.id)
    assert dataset.dict[2]["replaced_by"] == ""

    assert dataset.dict[3]["id"] == str(unreplaced_device_2.id)
    assert dataset.dict[3]["replaces"] == ""
    assert dataset.dict[3]["replaced_by"] == ""


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__create__old_is_marked_replaced(model, factory, resource, format):
    old_device = factory()
    dataset = get_import_dataset(resource, format=format, delete_columns=["id"])
    dataset.append_col([str(old_device.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=True)
    old_device.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["new"] == 1
    assert model.objects.count() == 2

    new_device_id = result.rows[0].object_id
    new_device = model.objects.get(id=new_device_id)
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device
    assert old_device.replaced_by == new_device
    assert old_device.replaces is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__old_is_marked_replaced(model, factory, resource, format):
    old_device = factory()
    new_device = factory(location=test_point_2_3d)

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["replaces"],
        queryset=model.objects.filter(id=new_device.id),
    )
    dataset.append_col([str(old_device.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=True)
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["update"] == 1
    assert model.objects.count() == 2
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device
    assert old_device.replaced_by == new_device
    assert old_device.replaces is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__change_replaced(model, factory, resource, format):
    old_device1 = factory(location=test_point_3d)
    old_device2 = factory(location=test_point_2_3d)
    new_device = factory(location=test_point_3_3d, replaces=old_device1)

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["replaces"],
        queryset=model.objects.filter(id=new_device.id),
    )
    dataset.append_col([str(old_device2.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=True)
    old_device1.refresh_from_db()
    old_device2.refresh_from_db()
    new_device.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["update"] == 1
    assert model.objects.count() == 3
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device2
    assert old_device1.replaced_by is None
    assert old_device1.replaces is None
    assert old_device2.replaced_by == new_device
    assert old_device2.replaces is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__remove_replacement(model, factory, resource, format):
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_2_3d, replaces=old_device)

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["replaces"],
        queryset=model.objects.filter(id=new_device.id),
    )
    dataset.append_col([None], header="replaces")

    result = resource().import_data(dataset, raise_errors=True)
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["update"] == 1
    assert model.objects.count() == 2
    assert new_device.replaced_by is None
    assert new_device.replaces is None
    assert old_device.replaced_by is None
    assert old_device.replaces is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize("has_replaces_column", [True, False], ids=["has_replaces_column", "no_replaces_column"])
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__without_replacement_should_not_affect(
    model,
    factory,
    resource,
    has_replaces_column,
    format,
):
    old_device = factory(location=test_point_3d)
    new_device = factory(location=test_point_2_3d, replaces=old_device)

    delete_columns = ["location"] if has_replaces_column else ["location", "replaces"]
    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=delete_columns,
        queryset=model.objects.filter(id=new_device.id),
    )
    dataset.append_col([test_point_3_3d], header="location")

    result = resource().import_data(dataset, raise_errors=True)
    old_device.refresh_from_db()
    new_device.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["update"] == 1
    assert model.objects.count() == 2
    assert new_device.replaced_by is None
    assert new_device.replaces == old_device
    assert old_device.replaced_by == new_device
    assert old_device.replaces is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(
    ("plan_model", "plan_factory", "plan_relation_name", "real_factory", "resource"),
    plan_model_plan_factory_plan_relation_name_real_factory_resource,
)
@pytest.mark.django_db
def test__device_plan_replace_import__create__real_devices_plan_is_updated_to_replacer(
    plan_model,
    plan_factory,
    plan_relation_name,
    real_factory,
    resource,
    format,
):
    old_device_plan = plan_factory()
    device_real = real_factory(**{plan_relation_name: old_device_plan})

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["id", "replaces"],
        queryset=plan_model.objects.filter(id=old_device_plan.id),
    )
    dataset.append_col([str(old_device_plan.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=True)
    old_device_plan.refresh_from_db()
    device_real.refresh_from_db()

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert result.totals["new"] == 1
    new_device_id = result.rows[0].object_id
    assert getattr(device_real, plan_relation_name).id == new_device_id


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__create__cannot_replace_already_replaced(model, factory, resource, format):
    replaced_device = factory(location=test_point_2_3d)
    newer_device = factory(location=test_point_3d, replaces=replaced_device)

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["id"],
        queryset=model.objects.filter(id=newer_device.id),
    )

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    newer_device.refresh_from_db()
    replaced_device.refresh_from_db()

    assert result.has_validation_errors()
    assert replaced_device.replaced_by == newer_device
    assert newer_device.replaced_by is None
    assert model.objects.count() == 2


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__cannot_replace_self(model, factory, resource, format):
    device = factory()

    dataset = get_import_dataset(
        resource,
        delete_columns=["replaces"],
        format=format,
    )
    dataset.append_col([str(device.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    device.refresh_from_db()

    assert result.has_validation_errors()
    assert not result.has_errors()
    assert device.replaces is None
    assert device.replaced_by is None


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.parametrize(("model", "factory", "resource"), model_factory_resource)
@pytest.mark.django_db
def test__device_plan_replace_import__update__cannot_make_circular_replacement(model, factory, resource, format):
    device_1 = factory(location=test_point_3d)
    device_2 = factory(location=test_point_2_3d, replaces=device_1)
    device_3 = factory(location=test_point_3_3d, replaces=device_2)

    dataset = get_import_dataset(
        resource,
        format=format,
        delete_columns=["replaces"],
        queryset=model.objects.filter(id=device_1.id),
    )
    dataset.append_col([str(device_3.id)], header="replaces")

    result = resource().import_data(dataset, raise_errors=False, collect_failed_rows=True)
    device_1.refresh_from_db()
    device_2.refresh_from_db()
    device_3.refresh_from_db()

    assert result.has_validation_errors()
    assert not result.has_errors()
    assert device_1.replaced_by == device_2
    assert device_2.replaced_by == device_3
    assert device_3.replaced_by is None
