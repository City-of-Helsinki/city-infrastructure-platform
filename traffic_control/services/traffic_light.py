from traffic_control.models import (
    TrafficLightPlan,
    TrafficLightPlanReplacement,
    TrafficLightReal,
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


def traffic_light_plan_get_active():
    return device_plan_get_active(TrafficLightPlan)


def traffic_light_plan_get_current():
    return device_plan_get_current(TrafficLightPlan)


def traffic_light_plan_create(data: dict) -> TrafficLightPlan:
    return device_plan_create(
        model=TrafficLightPlan,
        replace_method=traffic_light_plan_replace,
        data=data,
    )


def traffic_light_plan_update(instance: TrafficLightPlan, data: dict) -> TrafficLightPlan:
    return device_plan_update(
        model=TrafficLightPlan,
        replace_method=traffic_light_plan_replace,
        unreplace_method=traffic_light_plan_unreplace,
        instance=instance,
        data=data,
    )


def traffic_light_plan_replace(*, old: TrafficLightPlan, new: TrafficLightPlan):
    device_plan_replace(
        real_model=TrafficLightReal,
        plan_relation_name="traffic_light_plan",
        replacement_model=TrafficLightPlanReplacement,
        unreplace_method=traffic_light_plan_unreplace,
        old=old,
        new=new,
    )


def traffic_light_plan_unreplace(instance: TrafficLightPlan):
    device_plan_unreplace(replacement_model=TrafficLightPlanReplacement, instance=instance)


def traffic_light_plan_soft_delete(instance: TrafficLightPlan, user: User):
    device_plan_soft_delete(
        real_model=TrafficLightReal,
        plan_relation_name="traffic_light_plan",
        unreplace_method=traffic_light_plan_unreplace,
        instance=instance,
        user=user,
    )
