from typing import Callable, Type
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model

from traffic_control.mixins.models import SoftDeleteModel
from users.models import User


def device_plan_get_active(model: Type[SoftDeleteModel]):
    """Return a queryset of all not-soft-deleted device plans of given model"""
    return model.objects.active()


def device_plan_get_current(model: Type[SoftDeleteModel]):
    """Return a queryset of active non-replaced device plans of given model"""
    return device_plan_get_active(model).filter(replacement_to_new__isnull=True)


def _get_replaced_device(device_id: UUID, model: Type[SoftDeleteModel]) -> SoftDeleteModel:
    """Get a device plan for replacement by its ID. If the device plan does not exist, raise a ValidationError."""
    try:
        replaced_device = model.objects.get(pk=device_id)
        return replaced_device
    except model.DoesNotExist:
        raise ValidationError({"replaces": "The device plan to be replaced does not exist"})


@transaction.atomic
def device_plan_create(
    *,
    model: Type[SoftDeleteModel],
    replace_method: Callable,
    data: dict,
):
    """
    A generic method to create a new device plan in an atomic transaction.
    This method can be used to implement concrete create methods for different device plan types.

    If the 'replaces' key is present in the data, the method will replace the given device plan with the new one.
    The method also creates a new device plan instance with the provided data.

    :param model: The model of the device plan to be created.
    :param replace_method: A function to replace a device plan.
    :param data: A dictionary containing the data for the new device plan.
    :return: The newly created device plan instance.
    """
    replaced_device = data.pop("replaces", None)

    new_device_plan = model.objects.create(**data)

    if replaced_device:
        if not isinstance(replaced_device, model):
            replaced_device = _get_replaced_device(replaced_device, model)
        replace_method(old=replaced_device, new=new_device_plan)

    return new_device_plan


@transaction.atomic
def device_plan_update(
    *,
    model: Type[SoftDeleteModel],
    replace_method: Callable,
    unreplace_method: Callable,
    instance: SoftDeleteModel,
    data: dict,
):
    """
    A generic method to update a device plan in an atomic transaction.
    This method can be used to implement concrete update methods for different device plan types.

    If the `replaces` key is present in the data, the method will replace the given device plan with the new one.
    The method also updates the attributes of the device plan instance with the provided data.

    :param model: The model of the device plan to be updated.
    :param replace_method: A function to replace a device plan.
    :param unreplace_method: A function to undo a replacement.
    :param instance: The instance of the device plan to be updated.
    :param data: A dictionary containing the new data for the device plan.
    :raises ValidationError: If the replacement cannot be performed between the given device plans.
    :return: The updated device plan instance.
    """
    if "replaces" in data:
        replaced_device = data.pop("replaces")
        if replaced_device and not isinstance(replaced_device, model):
            replaced_device = _get_replaced_device(replaced_device, model)

        if replaced_device:
            replace_method(old=replaced_device, new=instance)
        else:
            unreplace_method(instance)

    for data_key, data_value in data.items():
        setattr(instance, data_key, data_value)
    instance.save()

    return instance


@transaction.atomic
def device_plan_replace(
    *,
    old: SoftDeleteModel,
    new: SoftDeleteModel,
    real_model: Type[SoftDeleteModel],
    plan_relation_name: str,
    replacement_model: Type[Model],
    unreplace_method: Callable,
):
    """
    A generic method to replace an old device plan with a new one in an atomic transaction.
    This method can be used to implement concrete replace methods for different device plan types.

    This function checks for valid replacements, removes older replacements if necessary,
    creates a new replacement, and updates the relevant real model object.

    :param old: The old device plan to be replaced.
    :param new: The new device plan that will replace the old one.
    :param real_model: The corresponding real device model that "realizes" the device plan.
    :param plan_relation_name: The name of the relation in the real model that refers to the device plan.
    :param replacement_model: The model of replacement in the device plans.
    :param unreplace_method: A function to undo a replacement.
    :raises ValidationError: If the replacement cannot be performed between the given device plans.
    """
    if old.replaced_by:
        raise ValidationError("Cannot replace a device plan that is already replaced")
    if old == new:
        raise ValidationError("Cannot replace a device plan with itself")
    check_replaced = old.replaces
    while check_replaced:
        if check_replaced == new:
            raise ValidationError("Cannot form a circular replacement chain")
        check_replaced = check_replaced.replaces

    # Remove older replacement in case of update
    if new.replaces:
        unreplace_method(new)

    replacement_model.objects.create(old=old, new=new)

    # Update relevant real(s)
    real_model.objects.filter(**{plan_relation_name: old}).update(**{plan_relation_name: new})


@transaction.atomic
def device_plan_unreplace(*, replacement_model: Type[Model], instance: SoftDeleteModel):
    """
    A generic method to undo a replacement of a device plan in an atomic transaction.
    This method can be used to implement concrete unreplace methods for different device plan types.

    :param replacement_model: The model of replacement in the device plans.
    :param instance: The instance of the device plan that currently replaces another device plan.
    :raises ValidationError: If the device plan does not replace another device plan.
    """
    if not instance.replaces:
        raise ValidationError("This device plan does not replace another device plan")
    replacement_model.objects.filter(new=instance).delete()
    instance.refresh_from_db()


@transaction.atomic
def device_plan_soft_delete(
    *,
    real_model: Type[SoftDeleteModel],
    plan_relation_name: str,
    unreplace_method: Callable,
    instance: SoftDeleteModel,
    user: User,
):
    """
    A generic method to perform soft-delete to device plan in an atomic transaction.
    This method can be used to implement concrete soft delete methods for different device plan types.

    This function updates the relevant real model object to remove the reference to the soft-deleted device plan
    and removes the replacement if the device plan is replaced.

    :param real_model: The corresponding real device model that "realizes" the device plan.
    :param plan_relation_name: The name of the relation in the real model that refers to the device plan.
    :param unreplace_method: A function to undo a replacement.
    :param instance: The instance of the device plan to be soft deleted.
    :param user: The user who is performing the soft delete operation.
    """
    replaced = instance.replaces
    if replaced:
        real_model.objects.filter(**{plan_relation_name: instance}).update(**{plan_relation_name: replaced})
        unreplace_method(instance)
    else:
        real_model.objects.filter(**{plan_relation_name: instance}).update(**{plan_relation_name: None})
    instance.soft_delete(user)


def get_all_replaced_plans(plan_model):
    return plan_model.objects.exclude(replacement_to_new__isnull=True)


def get_all_not_replaced_plans(plan_model):
    return plan_model.objects.filter(replacement_to_new__isnull=True)
