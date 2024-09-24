import pytest

from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignPlanReplacement,
    AdditionalSignReal,
    BarrierPlan,
    BarrierPlanReplacement,
    BarrierReal,
    MountPlan,
    MountPlanReplacement,
    MountReal,
    RoadMarkingPlan,
    RoadMarkingPlanReplacement,
    RoadMarkingReal,
    SignpostPlan,
    SignpostPlanReplacement,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightPlanReplacement,
    TrafficLightReal,
    TrafficSignPlan,
    TrafficSignPlanReplacement,
    TrafficSignReal,
)
from traffic_control.services.common import (
    device_plan_replace,
    get_all_not_replaced_plans,
    get_all_replaced_plans,
)
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    BarrierPlanFactory,
    MountPlanFactory,
    RoadMarkingPlanFactory,
    SignpostPlanFactory,
    TrafficLightPlanFactory,
    TrafficSignPlanFactory,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("real_model", "plan_model", "plan_replacement_model", "plan_factory", "plan_relation_name"),
    (
        (
            AdditionalSignReal,
            AdditionalSignPlan,
            AdditionalSignPlanReplacement,
            AdditionalSignPlanFactory,
            "additional_sign_plan",
        ),
        (BarrierReal, BarrierPlan, BarrierPlanReplacement, BarrierPlanFactory, "barrier_plan"),
        (MountReal, MountPlan, MountPlanReplacement, MountPlanFactory, "mount_plan"),
        (RoadMarkingReal, RoadMarkingPlan, RoadMarkingPlanReplacement, RoadMarkingPlanFactory, "road_marking_plan"),
        (SignpostReal, SignpostPlan, SignpostPlanReplacement, SignpostPlanFactory, "signpost_plan"),
        (
            TrafficLightReal,
            TrafficLightPlan,
            TrafficLightPlanReplacement,
            TrafficLightPlanFactory,
            "traffic_light_plan",
        ),
        (TrafficSignReal, TrafficSignPlan, TrafficSignPlanReplacement, TrafficSignPlanFactory, "traffic_sign_plan"),
    ),
)
def test_get_all_replaced_plan_ids(real_model, plan_model, plan_replacement_model, plan_factory, plan_relation_name):
    old = plan_factory()
    new = plan_factory()
    device_plan_replace(
        old=old,
        new=new,
        real_model=real_model,
        replacement_model=plan_replacement_model,
        plan_relation_name=plan_relation_name,
        unreplace_method=lambda x: x,
    )

    replaced_ids = get_all_replaced_plans(plan_model)
    assert replaced_ids.count() == 1
    assert replaced_ids.first().id == old.id

    not_replaced_ids = get_all_not_replaced_plans(plan_model)
    assert not_replaced_ids.count() == 1
    assert not_replaced_ids.first().id == new.id
