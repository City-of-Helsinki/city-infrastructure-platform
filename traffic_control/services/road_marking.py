from traffic_control.models import (
    RoadMarkingPlan,
    RoadMarkingPlanReplacement,
    RoadMarkingReal,
)
from traffic_control.services.common import (
    device_plan_create,
    device_plan_get_active,
    device_plan_get_current,
    device_plan_replace,
    device_plan_soft_delete,
    device_plan_unreplace,
    device_plan_update,
)
from users.models import User


def road_marking_plan_get_active():
    return device_plan_get_active(RoadMarkingPlan)


def road_marking_plan_get_current():
    return device_plan_get_current(RoadMarkingPlan)


def road_marking_plan_create(data: dict) -> RoadMarkingPlan:
    return device_plan_create(
        model=RoadMarkingPlan,
        replace_method=road_marking_plan_replace,
        data=data,
    )


def road_marking_plan_update(instance: RoadMarkingPlan, data: dict) -> RoadMarkingPlan:
    return device_plan_update(
        model=RoadMarkingPlan,
        replace_method=road_marking_plan_replace,
        unreplace_method=road_marking_plan_unreplace,
        instance=instance,
        data=data,
    )


def road_marking_plan_replace(*, old: RoadMarkingPlan, new: RoadMarkingPlan):
    device_plan_replace(
        real_model=RoadMarkingReal,
        plan_relation_name="road_marking_plan",
        replacement_model=RoadMarkingPlanReplacement,
        unreplace_method=road_marking_plan_unreplace,
        old=old,
        new=new,
    )


def road_marking_plan_unreplace(instance: RoadMarkingPlan):
    device_plan_unreplace(replacement_model=RoadMarkingPlanReplacement, instance=instance)


def road_marking_plan_soft_delete(instance: RoadMarkingPlan, user: User):
    device_plan_soft_delete(
        real_model=RoadMarkingReal,
        plan_relation_name="road_marking_plan",
        unreplace_method=road_marking_plan_unreplace,
        instance=instance,
        user=user,
    )
