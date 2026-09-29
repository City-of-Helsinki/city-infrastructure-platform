from datetime import timedelta
from typing import Callable, Type
from uuid import UUID

from django.contrib.gis.db.models.functions import Distance
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, IntegerField, Model, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Now

from traffic_control.enums import Lifecycle
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
    Also updates the validity period end date of the old device plan if applicable.

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
    if hasattr(old, "validity_period_end"):
        old.validity_period_end = new.validity_period_start - timedelta(days=1) if new.validity_period_start else None
        old.save(update_fields=["validity_period_end"])
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


def get_lifecycle_queryset(base_queryset):
    """
    Returns a queryset filtered by lifecycle:
    - lifecycle is ACTIVE or TEMPORARILY_ACTIVE
    """
    return base_queryset.filter(Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE))


def _model_has_validity_period(model: Type[Model]) -> bool:
    """Check whether the given model has validity period fields.

    Args:
        model (Type[Model]): The model to inspect.

    Returns:
        bool: True when the model defines both validity period fields.
    """
    field_names = {field.name for field in model._meta.get_fields()}
    return {"validity_period_start", "validity_period_end"}.issubset(field_names)


def _get_current_validity_period_q(model: Type[Model]) -> Q:
    """Build a Q object matching rows whose validity period is currently ongoing.

    The current time is resolved by the database (``Now()``) instead of Python, so the condition
    stays correct also for expressions and querysets that are built once at import time, e.g. the
    WFS feature types.

    Args:
        model (Type[Model]): The model the condition is built for.

    Returns:
        Q: The validity period condition, or an empty Q when the model has no validity period.
    """
    if not _model_has_validity_period(model):
        return Q()

    return _build_current_validity_period_q()


def _build_current_validity_period_q() -> Q:
    """Build the condition matching rows whose validity period is currently ongoing.

    Returns:
        Q: The validity period condition.
    """
    return Q(
        Q(validity_period_start__isnull=True) | Q(validity_period_start__lte=Now()),
        Q(validity_period_end__isnull=True) | Q(validity_period_end__gte=Now()),
    )


def get_validity_period_queryset(base_queryset):
    """
    Returns a queryset filtered by validity period:
    - validity_period_start is null or in the past
    - validity_period_end is null or in the future
    """
    return base_queryset.filter(_build_current_validity_period_q())


def get_lifecycle_and_validity_period_queryset(base_queryset):
    """
    Returns a queryset filtered by lifecycle and validity period.
    """
    return get_lifecycle_queryset(get_validity_period_queryset(base_queryset))


def get_real_count_subquery(real_model: Type[SoftDeleteModel], plan_relation_name: str) -> Coalesce:
    """Build an annotation expression counting the reals that realize a device plan.

    Only reals that are not soft deleted, have an active lifecycle and (when the model supports
    validity periods) an ongoing validity period are counted. Plans without any matching real get
    a count of 0 instead of NULL.

    Args:
        real_model (Type[SoftDeleteModel]): The real device model referencing the plan.
        plan_relation_name (str): Name of the foreign key on the real model pointing to the plan.

    Returns:
        Coalesce: An expression usable in ``QuerySet.annotate()`` on the plan model.
    """
    reals = (
        real_model.objects.active()
        .filter(
            _get_current_validity_period_q(real_model),
            Q(lifecycle=Lifecycle.ACTIVE) | Q(lifecycle=Lifecycle.TEMPORARILY_ACTIVE),
            **{plan_relation_name: OuterRef("pk")},
        )
        .order_by()
        .values(plan_relation_name)
        .annotate(real_count=Count("*"))
        .values("real_count")
    )

    return Coalesce(Subquery(reals, output_field=IntegerField()), 0)


def get_distance_to_plan_expression(plan_relation_name: str) -> Distance:
    """Build an annotation expression measuring how far a real device is from its plan.

    The distance is measured in the coordinate system's units (metres in EPSG:3879) between the
    full geometries. PostGIS' ``ST_Distance`` is two-dimensional, so the Z coordinate of the 3D
    location columns is ignored. Reals without a linked plan get NULL.

    Args:
        plan_relation_name (str): Name of the foreign key on the real model pointing to the plan.

    Returns:
        Distance: An expression usable in ``QuerySet.annotate()`` on the real model.
    """
    return Distance("location", f"{plan_relation_name}__location")
