from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignPlanReplacement,
    AdditionalSignReal,
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


def additional_sign_plan_get_active():
    return device_plan_get_active(AdditionalSignPlan)


def additional_sign_plan_get_current():
    return device_plan_get_current(AdditionalSignPlan)


def additional_sign_plan_create(data: dict) -> AdditionalSignPlan:
    return device_plan_create(
        model=AdditionalSignPlan,
        replace_method=additional_sign_plan_replace,
        data=data,
    )


def additional_sign_plan_update(instance: AdditionalSignPlan, data: dict) -> AdditionalSignPlan:
    return device_plan_update(
        model=AdditionalSignPlan,
        replace_method=additional_sign_plan_replace,
        unreplace_method=additional_sign_plan_unreplace,
        instance=instance,
        data=data,
    )


def additional_sign_plan_replace(*, old: AdditionalSignPlan, new: AdditionalSignPlan):
    device_plan_replace(
        real_model=AdditionalSignReal,
        plan_relation_name="additional_sign_plan",
        replacement_model=AdditionalSignPlanReplacement,
        unreplace_method=additional_sign_plan_unreplace,
        old=old,
        new=new,
    )


def additional_sign_plan_unreplace(instance: AdditionalSignPlan):
    device_plan_unreplace(replacement_model=AdditionalSignPlanReplacement, instance=instance)


def additional_sign_plan_soft_delete(instance: AdditionalSignPlan, user: User):
    device_plan_soft_delete(
        real_model=AdditionalSignReal,
        plan_relation_name="additional_sign_plan",
        unreplace_method=additional_sign_plan_unreplace,
        instance=instance,
        user=user,
    )
