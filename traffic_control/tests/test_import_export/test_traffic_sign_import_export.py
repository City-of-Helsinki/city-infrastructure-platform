import pytest

from traffic_control.models import TrafficSignReal
from traffic_control.resources.traffic_sign import TrafficSignPlanToRealTemplateResource, TrafficSignRealResource
from traffic_control.tests.factories import (
    get_mount_plan,
    get_mount_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
    TrafficSignRealFactory,
)


@pytest.mark.django_db
def test__traffic_sign_real__export():
    obj = TrafficSignRealFactory()
    dataset = TrafficSignRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name
    assert dataset.dict[0]["source_name"] == obj.source_name
    assert dataset.dict[0]["source_id"] == obj.source_id


@pytest.mark.django_db
def test__traffic_sign_real__import():
    TrafficSignRealFactory()
    dataset = TrafficSignRealResource().export()
    TrafficSignReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = TrafficSignRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert TrafficSignReal.objects.all().count() == 1


@pytest.mark.parametrize("has_mount_plan", (True, False), ids=lambda x: "mount_plan" if x else "no_mount_plan")
@pytest.mark.parametrize("has_mount_real", (True, False), ids=lambda x: "mount_real" if x else "no_mount_real")
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__traffic_sign_plan_export_real_import(has_mount_plan, has_mount_real, real_preexists):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None

    plan_obj = get_traffic_sign_plan(mount_plan=mount_plan)
    real_obj = get_traffic_sign_real(traffic_sign_plan=plan_obj) if real_preexists else None

    exported_dataset = TrafficSignPlanToRealTemplateResource().export()

    real = exported_dataset.dict[0]
    assert real["traffic_sign_plan__id"] == plan_obj.id

    if has_mount_plan and has_mount_real:
        assert real["mount_real__id"] == mount_real.id
    else:
        assert real["mount_real__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None
