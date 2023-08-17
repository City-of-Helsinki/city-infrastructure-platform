import datetime
import uuid
from typing import Optional

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureTarget,
    FurnitureSignpostPlan,
    FurnitureSignpostReal,
    FurnitureSignpostRealOperation,
)
from traffic_control.tests.factories import (
    get_mount_type,
    get_operation_type,
    get_owner,
    get_responsible_entity,
    get_user,
)
from traffic_control.tests.test_base_api_3d import test_point_3d


def get_city_furniture_color(name="Color", rgb="#FFFFFF") -> CityFurnitureColor:
    return CityFurnitureColor.objects.get_or_create(name=name, defaults=dict(rgb=rgb))[0]


def get_city_furniture_target(
    name_fi: str = "Turun tuomiokirkko",
    name_sw: Optional[str] = "Åbo domkyrka",
    name_en: Optional[str] = "Turku Cathedral",
    description: Optional[str] = (
        "Turun tuomiokirkko on Suomen Turussa I kaupunginosassa Aurajoen rannalla sijaitseva, "
        "monessa vaiheessa rakennettu kivikirkko, joka on suurimmaksi osaksi keskiajalta."
    ),
    source_id: Optional[str] = "Turun_tuomiokirkko",
    source_name: Optional[str] = "Wikipedia",
) -> CityFurnitureTarget:
    return CityFurnitureTarget.objects.get_or_create(
        name_fi=name_fi,
        defaults=dict(
            name_sw=name_sw,
            name_en=name_en,
            description=description,
            source_id=source_id,
            source_name=source_name,
        ),
    )[0]


def get_city_furniture_device_type(
    code: str = "CODE",
    class_type: str = "1030",
    function_type: str = "1090",
    target_model: Optional[CityFurnitureDeviceTypeTargetModel] = None,
) -> CityFurnitureDeviceType:
    return CityFurnitureDeviceType.objects.get_or_create(
        code=code,
        defaults=dict(
            class_type=class_type,
            function_type=function_type,
            target_model=target_model,
        ),
    )[0]


def get_furniture_signpost_plan(
    location=None,
    owner=None,
    device_type=None,
    parent=None,
    mount_plan=None,
    location_name_en=None,
) -> FurnitureSignpostPlan:
    user = get_user("test_user")
    location = location or test_point_3d
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostPlan.objects.get_or_create(
        location=location,
        location_name_en=location_name_en,
        owner=owner,
        device_type=device_type,
        direction=90,
        mount_type=get_mount_type(),
        mount_plan=mount_plan,
        source_name="Some_source",
        source_id=uuid.uuid4(),
        responsible_entity=get_responsible_entity(),
        parent=parent,
        created_by=user,
        updated_by=user,
    )[0]


def get_furniture_signpost_real(
    location=None,
    owner=None,
    device_type=None,
    furniture_signpost_plan=None,
    parent=None,
    mount_real=None,
    location_name_en=None,
) -> FurnitureSignpostReal:
    user = get_user("test_user")
    location = location or test_point_3d
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostReal.objects.get_or_create(
        furniture_signpost_plan=(
            furniture_signpost_plan
            or get_furniture_signpost_plan(location=location, owner=owner, device_type=device_type)
        ),
        location=location,
        location_name_en=location_name_en,
        owner=owner,
        device_type=device_type,
        direction=90,
        mount_type=get_mount_type(),
        mount_real=mount_real,
        installation_date=datetime.date(2020, 1, 20),
        source_name="Some_source",
        source_id=uuid.uuid4(),
        responsible_entity=get_responsible_entity(),
        parent=parent,
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
