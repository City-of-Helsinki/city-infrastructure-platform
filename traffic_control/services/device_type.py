from typing import Optional, TypedDict
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist

from traffic_control.enums import DeviceTypeTargetModel, TrafficControlDeviceTypeType, TrafficControlDeviceTypeValidity
from traffic_control.models.common import TrafficControlDeviceType


class TrafficControlDeviceTypeT(TypedDict, total=False):
    code: str
    validity: Optional[TrafficControlDeviceTypeValidity]
    corresponding_valid_device_type: Optional[TrafficControlDeviceType]
    icon: Optional[str]
    description: Optional[str]
    value: Optional[str]
    unit: Optional[str]
    size: Optional[str]
    legacy_code: Optional[str]
    legacy_description: Optional[str]
    target_model: Optional[DeviceTypeTargetModel]
    type: Optional[TrafficControlDeviceTypeType]
    content_schema: Optional[dict]


class TrafficControlDeviceTypeCreateT(TypedDict, total=False):
    code: str
    validity: Optional[TrafficControlDeviceTypeValidity]
    corresponding_valid_device_type: Optional[TrafficControlDeviceType]
    icon: Optional[str]
    description: Optional[str]
    value: Optional[str]
    unit: Optional[str]
    size: Optional[str]
    legacy_code: Optional[str]
    legacy_description: Optional[str]
    target_model: Optional[DeviceTypeTargetModel]
    type: Optional[TrafficControlDeviceTypeType]
    content_schema: Optional[dict]


class TrafficControlDeviceTypeUpdateT(TypedDict, total=False):
    code: str
    validity: TrafficControlDeviceTypeValidity
    corresponding_valid_device_type: Optional[TrafficControlDeviceType]
    icon: str
    description: Optional[str]
    value: str
    unit: str
    size: str
    legacy_code: Optional[str]
    legacy_description: Optional[str]
    target_model: Optional[DeviceTypeTargetModel]
    type: Optional[TrafficControlDeviceTypeType]
    content_schema: Optional[dict]


def device_type_create(data: TrafficControlDeviceTypeCreateT) -> TrafficControlDeviceType:
    device_type = TrafficControlDeviceType(**data)
    device_type.full_clean()
    device_type.save()
    return device_type


def device_type_update(id: UUID, data: TrafficControlDeviceTypeUpdateT) -> TrafficControlDeviceType:
    try:
        device_type = TrafficControlDeviceType.objects.get(id=id)
    except TrafficControlDeviceType.DoesNotExist:
        raise ObjectDoesNotExist(detail=f"Traffic control device type with ID '{id}' was not found.")

    update_fields = []

    for field, value in data.items():
        if getattr(device_type, field) != value:
            setattr(device_type, field, value)
            update_fields.append(field)

    if update_fields:
        device_type.full_clean()
        device_type.save(update_fields=update_fields)

    return device_type
