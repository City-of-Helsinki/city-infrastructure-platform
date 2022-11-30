import pytest

from traffic_control.models import BarrierReal
from traffic_control.resources.barrier import BarrierPlanToRealTemplateResource, BarrierRealResource
from traffic_control.tests.factories import get_barrier_plan, get_barrier_real


@pytest.mark.django_db
def test__barrier_real__export():
    obj = get_barrier_real()
    dataset = BarrierRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["device_type__code"] == obj.device_type.code
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__barrier_real__import():
    get_barrier_real()
    dataset = BarrierRealResource().export()
    BarrierReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = BarrierRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert BarrierReal.objects.all().count() == 1


@pytest.mark.django_db
def test__barrier_plan_export_real_import():
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    plan_obj = get_barrier_plan()

    exported_dataset = BarrierPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["id"] is None
    assert real["barrier_plan__id"] == plan_obj.id
