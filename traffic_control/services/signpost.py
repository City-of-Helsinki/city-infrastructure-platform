from traffic_control.models import (
    SignpostPlan,
    SignpostPlanReplacement,
    SignpostReal,
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


def signpost_plan_get_active():
    return device_plan_get_active(SignpostPlan)


def signpost_plan_get_current():
    return device_plan_get_current(SignpostPlan)


def signpost_plan_create(data: dict) -> SignpostPlan:
    return device_plan_create(
        model=SignpostPlan,
        replace_method=signpost_plan_replace,
        data=data,
    )


def signpost_plan_update(instance: SignpostPlan, data: dict) -> SignpostPlan:
    return device_plan_update(
        model=SignpostPlan,
        replace_method=signpost_plan_replace,
        unreplace_method=signpost_plan_unreplace,
        instance=instance,
        data=data,
    )


def signpost_plan_replace(*, old: SignpostPlan, new: SignpostPlan):
    device_plan_replace(
        real_model=SignpostReal,
        plan_relation_name="signpost_plan",
        replacement_model=SignpostPlanReplacement,
        unreplace_method=signpost_plan_unreplace,
        old=old,
        new=new,
    )


def signpost_plan_unreplace(instance: SignpostPlan):
    device_plan_unreplace(replacement_model=SignpostPlanReplacement, instance=instance)


def signpost_plan_soft_delete(instance: SignpostPlan, user: User):
    device_plan_soft_delete(
        real_model=SignpostReal,
        plan_relation_name="signpost_plan",
        unreplace_method=signpost_plan_unreplace,
        instance=instance,
        user=user,
    )
