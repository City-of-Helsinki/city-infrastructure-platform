from traffic_control.models import (
    TrafficSignPlan,
    TrafficSignPlanReplacement,
    TrafficSignReal,
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


def traffic_sign_plan_get_active():
    return device_plan_get_active(TrafficSignPlan)


def traffic_sign_plan_get_current():
    return device_plan_get_current(TrafficSignPlan)


def traffic_sign_plan_create(data: dict) -> TrafficSignPlan:
    return device_plan_create(
        model=TrafficSignPlan,
        replace_method=traffic_sign_plan_replace,
        data=data,
    )


def traffic_sign_plan_update(instance: TrafficSignPlan, data: dict) -> TrafficSignPlan:
    return device_plan_update(
        model=TrafficSignPlan,
        replace_method=traffic_sign_plan_replace,
        unreplace_method=traffic_sign_plan_unreplace,
        instance=instance,
        data=data,
    )


def traffic_sign_plan_replace(*, old: TrafficSignPlan, new: TrafficSignPlan):
    device_plan_replace(
        real_model=TrafficSignReal,
        plan_relation_name="traffic_sign_plan",
        replacement_model=TrafficSignPlanReplacement,
        unreplace_method=traffic_sign_plan_unreplace,
        old=old,
        new=new,
    )


def traffic_sign_plan_unreplace(instance: TrafficSignPlan):
    device_plan_unreplace(replacement_model=TrafficSignPlanReplacement, instance=instance)


def traffic_sign_plan_soft_delete(instance: TrafficSignPlan, user: User):
    device_plan_soft_delete(
        real_model=TrafficSignReal,
        plan_relation_name="traffic_sign_plan",
        unreplace_method=traffic_sign_plan_unreplace,
        instance=instance,
        user=user,
    )
