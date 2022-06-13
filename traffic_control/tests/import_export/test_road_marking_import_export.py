import pytest

from traffic_control.models import RoadMarkingReal
from traffic_control.resources.road_marking import RoadMarkingRealResource
from traffic_control.tests.factories import get_road_marking_real


@pytest.mark.django_db
def test__road_marking_real__export():
    obj = get_road_marking_real()
    dataset = RoadMarkingRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["device_type__code"] == obj.device_type.code
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name


@pytest.mark.django_db
def test__road_marking_real__import():
    get_road_marking_real()
    dataset = RoadMarkingRealResource().export()
    RoadMarkingReal.objects.all().delete()

    # Remove ID from data to create new objects
    obj_data = dataset.dict[0]
    obj_data.pop("id")
    dataset.dict = [obj_data]

    result = RoadMarkingRealResource().import_data(dataset, raise_errors=True)
    assert not result.has_errors()
    assert RoadMarkingReal.objects.all().count() == 1
