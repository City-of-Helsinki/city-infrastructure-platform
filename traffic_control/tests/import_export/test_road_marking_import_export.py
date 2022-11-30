import pytest

from traffic_control.models import RoadMarkingReal
from traffic_control.resources.road_marking import RoadMarkingPlanToRealTemplateResource, RoadMarkingRealResource
from traffic_control.tests.factories import (
    get_road_marking_plan,
    get_road_marking_real,
    get_traffic_sign_plan,
    get_traffic_sign_real,
)


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


@pytest.mark.parametrize(
    "has_traffic_sign_plan",
    (True, False),
    ids=lambda x: "traffic_sign_plan" if x else "no_traffic_sign_plan",
)
@pytest.mark.parametrize(
    "has_traffic_sign_real",
    (True, False),
    ids=lambda x: "traffic_sign_real" if x else "no_traffic_sign_real",
)
@pytest.mark.django_db
def test__road_marking_plan_export_real_import(has_traffic_sign_plan, has_traffic_sign_real):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    traffic_sign_plan = get_traffic_sign_plan() if has_traffic_sign_plan else None
    traffic_sign_real = get_traffic_sign_real() if has_traffic_sign_real else None

    plan_obj = get_road_marking_plan(traffic_sign_plan=traffic_sign_plan)

    exported_dataset = RoadMarkingPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["id"] is None
    assert real["road_marking_plan__id"] == plan_obj.id

    if has_traffic_sign_plan and has_traffic_sign_real:
        assert real["traffic_sign_real__id"] == traffic_sign_real.id
    else:
        assert real["traffic_sign_real__id"] is None
