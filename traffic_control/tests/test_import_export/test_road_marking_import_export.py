import pytest

from traffic_control.models import RoadMarkingReal
from traffic_control.resources.road_marking import RoadMarkingPlanToRealTemplateResource, RoadMarkingRealResource
from traffic_control.tests.factories import (
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)


@pytest.mark.django_db
def test__road_marking_real__export():
    obj = RoadMarkingRealFactory()
    dataset = RoadMarkingRealResource().export()

    assert dataset.dict[0]["location"] == str(obj.location)
    assert dataset.dict[0]["owner__name_fi"] == obj.owner.name_fi
    assert dataset.dict[0]["lifecycle"] == obj.lifecycle.name
    assert dataset.dict[0]["source_name"] == obj.source_name
    assert dataset.dict[0]["source_id"] == obj.source_id


@pytest.mark.django_db
def test__road_marking_real__import():
    RoadMarkingRealFactory()
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
@pytest.mark.parametrize("real_preexists", (True, False), ids=lambda x: "real_preexists" if x else "real_nonexists")
@pytest.mark.django_db
def test__road_marking_plan_export_real_import(has_traffic_sign_plan, has_traffic_sign_real, real_preexists):
    """Test that a plan object can be exported as its real object (referencing to the plan)"""

    traffic_sign_plan = TrafficSignPlanFactory() if has_traffic_sign_plan else None
    traffic_sign_real = TrafficSignRealFactory(traffic_sign_plan=traffic_sign_plan) if has_traffic_sign_real else None

    plan_obj = RoadMarkingPlanFactory(traffic_sign_plan=traffic_sign_plan)
    real_obj = RoadMarkingRealFactory(road_marking_plan=plan_obj) if real_preexists else None

    exported_dataset = RoadMarkingPlanToRealTemplateResource().export()
    assert len(exported_dataset) == 1

    real = exported_dataset.dict[0]
    assert real["road_marking_plan__id"] == plan_obj.id

    if has_traffic_sign_plan and has_traffic_sign_real:
        assert real["traffic_sign_real__id"] == traffic_sign_real.id
    else:
        assert real["traffic_sign_real__id"] is None

    if real_preexists:
        assert real["id"] == real_obj.id
    else:
        assert real["id"] is None
