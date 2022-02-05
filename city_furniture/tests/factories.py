import datetime
from typing import Optional

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal, FurnitureSignpostRealOperation
from city_furniture.models.common import CityFurnitureColor, CityFurnitureDeviceType
from traffic_control.tests.factories import get_operation_type, get_owner, get_user
from traffic_control.tests.test_base_api_3d import test_point_3d


def get_city_furniture_color(name="Color", rgb="#FFFFFF"):
    return CityFurnitureColor.objects.get_or_create(name=name, defaults=dict(rgb=rgb))[0]


def get_city_furniture_device_type(
    code: str = "CODE",
    class_type: str = "1030",
    function_type: str = "1090",
    target_model: Optional[CityFurnitureDeviceTypeTargetModel] = None,
):
    return CityFurnitureDeviceType.objects.get_or_create(
        code=code,
        defaults=dict(
            class_type=class_type,
            function_type=function_type,
            target_model=target_model,
        ),
    )[0]


def get_furniture_signpost_plan(location=test_point_3d, owner=None, device_type=None):
    user = get_user("test_user")
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostPlan.objects.get_or_create(
        location=location,
        owner=owner,
        device_type=device_type,
        created_by=user,
        updated_by=user,
    )[0]


def get_furniture_signpost_real(location=test_point_3d, owner=None, device_type=None):
    user = get_user("test_user")
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostReal.objects.get_or_create(
        location=location,
        owner=owner,
        device_type=device_type,
        created_by=user,
        updated_by=user,
    )[0]


def add_furniture_signpost_real_operation(furniture_signpost_real, operation_type=None, operation_date=None):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return FurnitureSignpostRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        furniture_signpost_real=furniture_signpost_real,
        created_by=user,
        updated_by=user,
    )