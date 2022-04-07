import datetime
import uuid
from typing import Optional

from django.urls import reverse

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel, OrganizationLevel
from city_furniture.models import FurnitureSignpostPlan, FurnitureSignpostReal, FurnitureSignpostRealOperation
from city_furniture.models.common import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureTarget,
    ResponsibleEntity,
)
from traffic_control.tests.factories import get_mount_type, get_operation_type, get_owner, get_user
from traffic_control.tests.test_base_api_3d import test_point_3d


def get_responsible_entity_person(name="Matti Meikäläinen"):
    division = ResponsibleEntity.objects.get_or_create(
        name="KYMP",
        defaults=dict(
            organization_level=OrganizationLevel.DIVISION,
        ),
    )[0]
    service = ResponsibleEntity.objects.get_or_create(
        name="Yleiset alueet",
        defaults=dict(
            parent=division,
            organization_level=OrganizationLevel.DIVISION,
        ),
    )[0]
    person = ResponsibleEntity.objects.get_or_create(
        name=name,
        defaults=dict(
            parent=service,
            organization_level=OrganizationLevel.PERSON,
        ),
    )[0]
    return person


def get_city_furniture_color(name="Color", rgb="#FFFFFF"):
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
):
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
):
    return CityFurnitureDeviceType.objects.get_or_create(
        code=code,
        defaults=dict(
            class_type=class_type,
            function_type=function_type,
            target_model=target_model,
        ),
    )[0]


def get_furniture_signpost_plan(location=None, owner=None, device_type=None):
    user = get_user("test_user")
    location = location or test_point_3d
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostPlan.objects.get_or_create(
        location=location,
        owner=owner,
        device_type=device_type,
        direction=90,
        mount_type=get_mount_type(),
        source_name="Some_source",
        source_id=uuid.uuid4(),
        project_id="ABC123",
        created_by=user,
        updated_by=user,
    )[0]


def get_furniture_signpost_real(location=None, owner=None, device_type=None):
    user = get_user("test_user")
    location = location or test_point_3d
    owner = owner or get_owner()
    device_type = device_type or get_city_furniture_device_type()

    return FurnitureSignpostReal.objects.get_or_create(
        furniture_signpost_plan=get_furniture_signpost_plan(location=location, owner=owner, device_type=device_type),
        location=location,
        owner=owner,
        device_type=device_type,
        direction=90,
        mount_type=get_mount_type(),
        installation_date=datetime.date(2020, 1, 20),
        source_name="Some_source",
        source_id=uuid.uuid4(),
        project_id="ABC123",
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


def get_wfs_url(model_name: str = "furnituresignpostreal", output_format: str = "application/gml+xml") -> str:
    url = f"{reverse('wfs-city-infrastructure')}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
    url += f"&TYPENAMES={model_name}&OUTPUTFORMAT={output_format}"
    return url
