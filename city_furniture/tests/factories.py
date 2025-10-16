import datetime
import uuid
from typing import Optional

import factory

from city_furniture.enums import CityFurnitureDeviceTypeTargetModel
from city_furniture.models import (
    CityFurnitureColor,
    CityFurnitureDeviceType,
    CityFurnitureDeviceTypeIcon,
    CityFurnitureTarget,
    FurnitureSignpostPlan,
    FurnitureSignpostReal,
    FurnitureSignpostRealOperation,
)
from traffic_control.tests.factories import (
    get_mount_type,
    get_operation_type,
    get_owner,
    get_user,
    MountPlanFactory,
    MountTypeFactory,
    OwnerFactory,
    PlanFactory,
    UserFactory,
)
from traffic_control.tests.test_base_api_3d import test_point_3d

DEFAULT_DEVICE_TYPE_DESCRIPTION = "DESCRIPTION_FI"


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


class CityFurnitureDeviceTypeIconFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CityFurnitureDeviceTypeIcon
        django_get_or_create = ("file",)

    file = factory.django.FileField(
        filename=factory.Sequence(lambda n: f"test_icon_{n}.svg"),
        data=b'<svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>',
    )


class CityFurnitureDeviceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CityFurnitureDeviceType
        django_get_or_create = ("code",)

    code = factory.sequence(lambda n: f"Code{n}")
    icon_file = factory.SubFactory(CityFurnitureDeviceTypeIconFactory)
    class_type = "1030"
    function_type = "1090"
    description_fi = factory.sequence(lambda n: "DescFI_{n}")
    target_model = None


def get_city_furniture_device_type(
    code: str = "CODE",
    class_type: str = "1030",
    function_type: str = "1090",
    target_model: Optional[CityFurnitureDeviceTypeTargetModel] = None,
    description_fi=DEFAULT_DEVICE_TYPE_DESCRIPTION,
) -> CityFurnitureDeviceType:
    return CityFurnitureDeviceType.objects.get_or_create(
        code=code,
        defaults=dict(
            class_type=class_type, function_type=function_type, target_model=target_model, description_fi=description_fi
        ),
    )[0]


class FurnitureSignpostPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FurnitureSignpostPlan
        django_get_or_create = (
            "source_id",
            "source_name",
        )

    location = test_point_3d
    location_name_en = factory.sequence(lambda n: f"Location {n}")
    owner = factory.SubFactory(OwnerFactory)
    device_type = factory.SubFactory(CityFurnitureDeviceTypeFactory)
    direction = 90
    mount_type = factory.SubFactory(MountTypeFactory)
    mount_plan = factory.SubFactory(MountPlanFactory)
    source_id = factory.Sequence(lambda n: f"SOURCE_ID_{n}")
    source_name = factory.Sequence(lambda n: f"SOURCE_NAME_{n}")
    responsible_entity = None
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(PlanFactory)


def get_furniture_signpost_plan(
    location=None,
    responsible_entity=None,
    owner=None,
    device_type=None,
    parent=None,
    mount_plan=None,
    location_name_en=None,
    plan=None,
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
        responsible_entity=responsible_entity,
        parent=parent,
        created_by=user,
        updated_by=user,
        plan=plan,
    )[0]


class FurnitureSignpostRealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FurnitureSignpostReal
        django_get_or_create = (
            "source_id",
            "source_name",
        )

    source_id = factory.Sequence(lambda n: f"SOURCE_ID_{n}")
    source_name = factory.Sequence(lambda n: f"SOURCE_NAME_{n}")
    device_type = factory.SubFactory(CityFurnitureDeviceTypeFactory)
    location = test_point_3d
    owner = factory.SubFactory(OwnerFactory)


def get_furniture_signpost_real(
    location=None,
    responsible_entity=None,
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
        responsible_entity=responsible_entity,
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
