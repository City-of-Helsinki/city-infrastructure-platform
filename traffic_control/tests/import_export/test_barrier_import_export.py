import pytest

from traffic_control.models import BarrierReal
from traffic_control.resources.barrier import BarrierRealResource
from traffic_control.tests.factories import get_barrier_real


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
