from traffic_control.models import (
    MountPlan,
    MountPlanReplacement,
    MountReal,
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


def mount_plan_get_active():
    return device_plan_get_active(MountPlan)


def mount_plan_get_current():
    return device_plan_get_current(MountPlan)


def mount_plan_create(data: dict) -> MountPlan:
    return device_plan_create(
        model=MountPlan,
        replace_method=mount_plan_replace,
        data=data,
    )


def mount_plan_update(instance: MountPlan, data: dict) -> MountPlan:
    return device_plan_update(
        model=MountPlan,
        replace_method=mount_plan_replace,
        unreplace_method=mount_plan_unreplace,
        instance=instance,
        data=data,
    )


def mount_plan_replace(*, old: MountPlan, new: MountPlan):
    device_plan_replace(
        real_model=MountReal,
        plan_relation_name="mount_plan",
        replacement_model=MountPlanReplacement,
        unreplace_method=mount_plan_unreplace,
        old=old,
        new=new,
    )


def mount_plan_unreplace(instance: MountPlan):
    device_plan_unreplace(replacement_model=MountPlanReplacement, instance=instance)


def mount_plan_soft_delete(instance: MountPlan, user: User):
    device_plan_soft_delete(
        real_model=MountReal,
        plan_relation_name="mount_plan",
        unreplace_method=mount_plan_unreplace,
        instance=instance,
        user=user,
    )
