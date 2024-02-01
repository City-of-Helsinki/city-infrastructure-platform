from traffic_control.models import (
    BarrierPlan,
    BarrierPlanReplacement,
    BarrierReal,
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


def barrier_plan_get_active():
    return device_plan_get_active(BarrierPlan)


def barrier_plan_get_current():
    return device_plan_get_current(BarrierPlan)


def barrier_plan_create(data: dict) -> BarrierPlan:
    return device_plan_create(
        model=BarrierPlan,
        replace_method=barrier_plan_replace,
        data=data,
    )


def barrier_plan_update(instance: BarrierPlan, data: dict) -> BarrierPlan:
    return device_plan_update(
        model=BarrierPlan,
        replace_method=barrier_plan_replace,
        unreplace_method=barrier_plan_unreplace,
        instance=instance,
        data=data,
    )


def barrier_plan_replace(*, old: BarrierPlan, new: BarrierPlan):
    device_plan_replace(
        real_model=BarrierReal,
        plan_relation_name="barrier_plan",
        replacement_model=BarrierPlanReplacement,
        unreplace_method=barrier_plan_unreplace,
        old=old,
        new=new,
    )


def barrier_plan_unreplace(instance: BarrierPlan):
    device_plan_unreplace(replacement_model=BarrierPlanReplacement, instance=instance)


def barrier_plan_soft_delete(instance: BarrierPlan, user: User):
    device_plan_soft_delete(
        real_model=BarrierReal,
        plan_relation_name="barrier_plan",
        unreplace_method=barrier_plan_unreplace,
        instance=instance,
        user=user,
    )
