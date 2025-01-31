import pytest

from traffic_control.models import BarrierReal
from traffic_control.resources.barrier import BarrierPlanToRealTemplateResource, BarrierRealResource
from traffic_control.tests.factories import BarrierPlanFactory, BarrierRealFactory


@pytest.mark.django_db
def test__barrier_real__export():
    obj = BarrierRealFactory()
    dataset = BarrierRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name
    assert dataset.dict[0]["source_name"] == obj.source_name
    assert dataset.dict[0]["source_id"] == obj.source_id


@pytest.mark.django_db
def test__barrier_real__import():
    BarrierRealFactory()
    dataset = BarrierRealResource().export()
    BarrierReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = BarrierRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert BarrierReal.objects.all().count() == 1


@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__barrier_plan_export_real_import(real_preexists):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    plan_obj = BarrierPlanFactory(source_name="SOURCE_NAME", source_id="SOURCE_ID")
    real_obj = (
        BarrierRealFactory(source_name="SOURCE_NAME", source_id="SOURCE_ID", barrier_plan=plan_obj)
        if real_preexists
        else None
    )

    exported_dataset = BarrierPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["barrier_plan__id"] == plan_obj.id

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None
