import pytest

from traffic_control.models import SignpostPlan, SignpostReal
from traffic_control.resources.signpost import SignpostPlanToRealTemplateResource, SignpostRealResource
from traffic_control.tests.factories import get_mount_plan, get_mount_real, get_signpost_plan, get_signpost_real
from traffic_control.tests.test_base_api import test_point_2


@pytest.mark.django_db
def test__signpost_real__export():
    obj = get_signpost_real()
    dataset = SignpostRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__signpost_real__import():
    get_signpost_real()
    dataset = SignpostRealResource().export()
    SignpostReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = SignpostRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert SignpostReal.objects.all().count() == 1


@pytest.mark.parametrize("has_mount_plan", (True, False), ids=lambda x: "mount_plan" if x else "no_mount_plan")
@pytest.mark.parametrize("has_mount_real", (True, False), ids=lambda x: "mount_real" if x else "no_mount_real")
@pytest.mark.parametrize("has_parent_plan", (True, False), ids=lambda x: "parent_plan" if x else "no_parent_plan")
@pytest.mark.parametrize("has_parent_real", (True, False), ids=lambda x: "parent_real" if x else "no_parent_real")
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__signpost_plan_export_real_import(
    has_mount_plan, has_mount_real, has_parent_plan, has_parent_real, real_preexists
):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    mount_plan = get_mount_plan() if has_mount_plan else None
    mount_real = get_mount_real() if has_mount_real else None
    parent_plan = get_signpost_plan() if has_parent_plan else None
    parent_real = get_signpost_real() if has_parent_real else None

    plan_obj = get_signpost_plan(location=test_point_2, mount_plan=mount_plan, parent=parent_plan)
    real_obj = get_signpost_real(location=test_point_2, signpost_plan=plan_obj) if real_preexists else None

    exported_dataset = SignpostPlanToRealTemplateResource().export(queryset=SignpostPlan.objects.filter(id=plan_obj.id))
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["signpost_plan__id"] == plan_obj.id

    if has_mount_plan and has_mount_real:
        assert real["mount_real__id"] == mount_real.id
    else:
        assert real["mount_real__id"] is None

    if has_parent_plan and has_parent_real:
        assert real["parent__id"] == parent_real.id
    else:
        assert real["parent__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None
