import datetime
from typing import Any, Optional

import factory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle, OrganizationLevel, TrafficControlDeviceTypeType
from traffic_control.models import (
    AdditionalSignPlan,
    AdditionalSignReal,
    AdditionalSignRealOperation,
    BarrierPlan,
    BarrierReal,
    BarrierRealOperation,
    ConnectionType,
    MountPlan,
    MountReal,
    MountRealOperation,
    MountType,
    OperationalArea,
    OperationType,
    Owner,
    Plan,
    PortalType,
    Reflective,
    ResponsibleEntity,
    RoadMarkingColor,
    RoadMarkingPlan,
    RoadMarkingReal,
    RoadMarkingRealOperation,
    SignpostPlan,
    SignpostReal,
    SignpostRealOperation,
    TrafficControlDeviceType,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightRealOperation,
    TrafficLightSoundBeaconValue,
    TrafficLightType,
    TrafficSignPlan,
    TrafficSignReal,
    TrafficSignRealOperation,
)
from traffic_control.services.additional_sign import additional_sign_plan_replace
from traffic_control.services.barrier import barrier_plan_replace
from traffic_control.services.mount import mount_plan_replace
from traffic_control.services.road_marking import road_marking_plan_replace
from traffic_control.services.signpost import signpost_plan_replace
from traffic_control.services.traffic_light import traffic_light_plan_replace
from traffic_control.services.traffic_sign import traffic_sign_plan_replace
from traffic_control.tests.test_base_api import test_multi_polygon, test_point, test_polygon
from traffic_control.tests.test_base_api_3d import test_point_3d
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"User{n}")
    password = "x"
    first_name = "John"
    last_name = "Doe"
    email = "test@example.com"
    is_staff = False
    is_superuser = False
    bypass_responsible_entity = False
    bypass_operational_area = False


def get_user(username=None, admin=False, bypass_operational_area=False, bypass_responsible_entity=False) -> User:
    return UserFactory(
        username=username,
        is_staff=admin,
        is_superuser=admin,
        bypass_operational_area=bypass_operational_area,
        bypass_responsible_entity=bypass_responsible_entity,
    )


def get_operational_area(area=None, name=None) -> OperationalArea:
    return OperationalArea.objects.get_or_create(
        name=name or "Test operational area",
        location=area or MultiPolygon(test_polygon, srid=settings.SRID),
    )[0]


class OwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Owner
        django_get_or_create = ("name_fi",)

    name_fi = factory.sequence(lambda n: f"Omistaja{n}")
    name_en = factory.sequence(lambda n: f"Owner{n}")


def get_owner(name_fi="Omistaja", name_en="Owner") -> Owner:
    return Owner.objects.get_or_create(name_fi=name_fi, name_en=name_en)[0]


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan

    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    name = "Test plan"
    decision_id = "2020_1"
    location = test_multi_polygon
    derive_location = False
    is_active = True
    source_id = factory.Sequence(lambda n: f"SOURCE_ID_{n}")
    source_name = factory.Sequence(lambda n: f"SOURCE_NAME_{n}")


def get_plan(location=test_multi_polygon, name="Test plan", derive_location=False) -> Plan:
    return PlanFactory(location=location, name=name, derive_location=derive_location)


def get_barrier_plan(
    location="",
    plan=None,
    device_type=None,
    responsible_entity=None,
    replaces=None,
) -> BarrierPlan:
    user = get_user("test_user")
    barrier_plan = BarrierPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )[0]

    if replaces:
        barrier_plan_replace(old=replaces, new=barrier_plan)

    return barrier_plan


def get_barrier_real(
    location="",
    device_type=None,
    responsible_entity=None,
    barrier_plan=None,
) -> BarrierReal:
    user = get_user("test_user")
    barrier_plan = barrier_plan or get_barrier_plan()

    return BarrierReal.objects.create(
        device_type=device_type,
        barrier_plan=barrier_plan,
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 20),
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )


class MountTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MountType
        django_get_or_create = ["code"]

    code = factory.Sequence(lambda n: f"MOUNT_TYPE_{n}")
    description = "Test mount type"
    description_fi = "Testi Kiinnityskohde tyyppi"
    digiroad_code = 1
    digiroad_description = "digiroad_desc"


def get_mount_type(code="POST", description="Post") -> MountType:
    return MountType.objects.get_or_create(code=code, description=description)[0]


class PortalTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PortalType
        django_get_or_create = ["structure", "build_type", "model"]

    structure = "Structure"
    build_type = "BuildType"
    model = "Model"


def get_portal_type(
    structure="Structure",
    build_type="Build type",
    model="Model",
) -> PortalType:
    return PortalType.objects.get_or_create(
        structure=structure,
        build_type=build_type,
        model=model,
    )[0]


def get_mount_plan(location="", plan=None, responsible_entity=None, replaces=None) -> MountPlan:
    user = get_user("test_user")

    mount_plan = MountPlan.objects.get_or_create(
        mount_type=get_mount_type(code="PORTAL", description="Portal"),
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )[0]

    if replaces:
        mount_plan_replace(old=replaces, new=mount_plan)

    return mount_plan


class MountRealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MountReal
        django_get_or_create = ("source_id", "source_name")

    location = test_point
    height = 1
    base = ""
    portal_type = factory.SubFactory(PortalTypeFactory)
    mount_type = factory.SubFactory(MountTypeFactory)
    material = "test material"
    validity_period_start = None
    validity_period_end = None
    txt = None
    electric_accountable = None
    is_foldable = None
    cross_bar_length = None
    road_name = None
    location_specifier = None
    mount_plan = None
    inspected_at = None
    diameter = None
    scanned_at = None
    source_id = factory.sequence(lambda n: f"MOUNT_REAL_source_id_{n}")
    source_name = "source_name"
    owner = factory.SubFactory(OwnerFactory)
    attachment_url = ""


def get_mount_real(location="", mount_plan=None, responsible_entity=None) -> MountReal:
    user = get_user("test_user")
    mount_plan = mount_plan or get_mount_plan()

    return MountReal.objects.get_or_create(
        mount_plan=mount_plan,
        mount_type=get_mount_type(code="PORTAL", description="Portal"),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_plan(
    location="",
    plan=None,
    device_type=None,
    traffic_sign_plan=None,
    responsible_entity=None,
    replaces=None,
) -> RoadMarkingPlan:
    user = get_user("test_user")

    road_marking_plan = RoadMarkingPlan.objects.get_or_create(
        device_type=device_type,
        value="30",
        color=RoadMarkingColor.WHITE,
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        material="Maali",
        is_grinded=True,
        is_raised=False,
        road_name="Testingroad",
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        traffic_sign_plan=traffic_sign_plan,
        created_by=user,
        updated_by=user,
    )[0]

    if replaces:
        road_marking_plan_replace(old=replaces, new=road_marking_plan)

    return road_marking_plan


def get_road_marking_real(
    location="",
    device_type=None,
    road_marking_plan=None,
    traffic_sign_real=None,
    responsible_entity=None,
) -> RoadMarkingReal:
    user = get_user("test_user")

    return RoadMarkingReal.objects.get_or_create(
        device_type=device_type,
        road_marking_plan=road_marking_plan or get_road_marking_plan(),
        value="30",
        color=RoadMarkingColor.WHITE,
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        material="Maali",
        is_grinded=True,
        is_raised=False,
        road_name="Testingroad",
        owner=get_owner(),
        responsible_entity=responsible_entity,
        traffic_sign_real=traffic_sign_real,
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_plan(
    location="",
    plan=None,
    device_type=None,
    parent=None,
    mount_plan=None,
    txt=None,
    responsible_entity=None,
    replaces=None,
) -> SignpostPlan:
    user = get_user("test_user")

    signpost_plan = SignpostPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        parent=parent,
        mount_plan=mount_plan,
        txt=txt,
        created_by=user,
        updated_by=user,
    )[0]

    if replaces:
        signpost_plan_replace(old=replaces, new=signpost_plan)

    return signpost_plan


def get_signpost_real(
    location="",
    device_type=None,
    signpost_plan=None,
    parent=None,
    mount_real=None,
    txt=None,
    responsible_entity=None,
) -> SignpostReal:
    user = get_user("test_user")

    return SignpostReal.objects.get_or_create(
        device_type=device_type,
        signpost_plan=signpost_plan or get_signpost_plan(),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        parent=parent,
        mount_real=mount_real,
        txt=txt,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_plan(
    location="",
    plan=None,
    device_type=None,
    mount_plan=None,
    responsible_entity=None,
    replaces=None,
) -> TrafficLightPlan:
    user = get_user("test_user")

    traffic_light_plan = TrafficLightPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point,
        type=TrafficLightType.SIGNAL,
        lifecycle=Lifecycle.ACTIVE,
        mount_type=get_mount_type(),
        mount_plan=mount_plan,
        road_name="Testingroad",
        sound_beacon=TrafficLightSoundBeaconValue.YES,
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )[0]

    if replaces:
        traffic_light_plan_replace(old=replaces, new=traffic_light_plan)

    return traffic_light_plan


def get_traffic_light_real(
    location="",
    device_type=None,
    traffic_light_plan=None,
    mount_real=None,
    responsible_entity=None,
) -> TrafficLightReal:
    user = get_user("test_user")

    return TrafficLightReal.objects.get_or_create(
        device_type=device_type,
        traffic_light_plan=traffic_light_plan or get_traffic_light_plan(),
        location=location or test_point,
        type=TrafficLightType.SIGNAL,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        mount_type=get_mount_type(),
        mount_real=mount_real,
        road_name="Testingroad",
        sound_beacon=TrafficLightSoundBeaconValue.YES,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
    )[0]


class TrafficControlDeviceTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TrafficControlDeviceType
        django_get_or_create = ["code"]

    code = factory.sequence(lambda n: str(n))
    icon = factory.sequence(lambda n: f"icon_{n}")
    description = factory.sequence(lambda n: f"description_{n}")
    value = factory.sequence(lambda n: f"value_{n}")
    unit = ""
    size = ""
    legacy_code = factory.sequence(lambda n: str(n))
    legacy_description = factory.sequence(lambda n: f"legacy_description_{n}")
    target_model = None
    type = None
    content_schema = None


def get_traffic_control_device_type(
    code: str = "A11",
    icon: str = "",
    description: str = "Test",
    value: str = "",
    unit: str = "",
    size: str = "",
    legacy_code: Optional[str] = None,
    legacy_description: Optional[str] = None,
    target_model: Optional[DeviceTypeTargetModel] = None,
    type: Optional[TrafficControlDeviceTypeType] = None,
    content_schema: Optional[Any] = None,
) -> TrafficControlDeviceType:
    dt = TrafficControlDeviceType.objects.get_or_create(
        code=code,
        icon=icon,
        description=description,
        value=value,
        unit=unit,
        size=size,
        legacy_code=legacy_code,
        legacy_description=legacy_description,
        target_model=target_model,
        type=type,
        content_schema=content_schema,
    )[0]
    dt.refresh_from_db()
    return dt


def get_traffic_sign_plan(
    location="",
    plan=None,
    device_type=None,
    mount_plan=None,
    responsible_entity=None,
    replaces=None,
) -> TrafficSignPlan:
    user = get_user("test_user")

    traffic_sign_plan = TrafficSignPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point_3d,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        mount_plan=mount_plan,
        created_by=user,
        updated_by=user,
    )[0]
    if replaces:
        traffic_sign_plan_replace(old=replaces, new=traffic_sign_plan)

    return traffic_sign_plan


class TrafficSignRealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TrafficSignReal
        django_get_or_create = ["source_id", "source_name"]

    source_id = factory.Sequence(lambda n: f"SOURCE_ID_{n}")
    source_name = factory.Sequence(lambda n: f"SOURCE_NAME_{n}")
    location = test_point
    device_type = factory.SubFactory(TrafficControlDeviceTypeFactory)
    road_name = None
    lane_number = None
    lane_type = None
    direction = None
    height = 1
    mount_type = factory.SubFactory(MountTypeFactory)
    value = None
    size = None
    reflection_class = None
    surface_class = None
    txt = None
    location_specifier = None
    validity_period_start = None
    validity_period_end = None
    seasonal_validity_period_start = None
    seasonal_validity_period_end = None
    owner = factory.SubFactory(OwnerFactory)
    traffic_sign_plan = None
    legacy_code = "TestLegacyCode"
    mount_real = factory.SubFactory(MountRealFactory)
    installation_id = factory.sequence(lambda n: f"installation_id{n}")
    installation_details = "Installaation details"
    permit_decision_id = factory.sequence(lambda n: f"permit_decision{n}")
    coverage_area = None
    scanned_at = None
    manufacturer = factory.sequence(lambda n: f"Manufacturer{n}")
    rfid = factory.sequence(lambda n: f"rfid{n}")
    operation = factory.sequence(lambda n: f"operation{n}")
    attachment_url = factory.sequence(lambda n: f"attachment_url{n}")


def get_traffic_sign_real(
    location="",
    device_type=None,
    traffic_sign_plan=None,
    mount_real=None,
    responsible_entity=None,
) -> TrafficSignReal:
    user = get_user("test_user")

    return TrafficSignReal.objects.get_or_create(
        traffic_sign_plan=traffic_sign_plan or get_traffic_sign_plan(),
        device_type=device_type,
        location=location or test_point_3d,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        responsible_entity=responsible_entity,
        mount_real=mount_real,
        created_by=user,
        updated_by=user,
    )[0]


def get_additional_sign_plan(
    location=test_point_3d,
    device_type=None,
    parent=None,
    mount_plan=None,
    owner=None,
    plan=None,
    content_s=None,
    missing_content=False,
    order=None,
    responsible_entity=None,
    replaces=None,
) -> AdditionalSignPlan:
    user = get_user("test_user")
    owner = owner or get_owner()

    kwargs = {}
    if order is not None:
        kwargs["order"] = order

    asp = AdditionalSignPlan.objects.get_or_create(
        parent=parent,
        mount_plan=mount_plan,
        location=location,
        device_type=device_type,
        owner=owner,
        responsible_entity=responsible_entity,
        plan=plan,
        created_by=user,
        updated_by=user,
        content_s=content_s,
        missing_content=missing_content,
        **kwargs,
    )[0]
    asp.refresh_from_db()

    if replaces:
        additional_sign_plan_replace(old=replaces, new=asp)

    return asp


class AdditionalSignRealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdditionalSignReal
        django_get_or_create = ["source_id", "source_name"]

    source_id = factory.Sequence(lambda n: f"SOURCE_ID_{n}")
    source_name = factory.Sequence(lambda n: f"SOURCE_NAME_{n}")
    device_type = factory.SubFactory(TrafficControlDeviceTypeFactory)
    order = factory.sequence(lambda n: n)
    content_s = None
    missing_content = True
    additional_information = ""
    location = test_point
    height = 1
    size = None
    direction = None
    reflection_class = None
    surface_class = None
    color = None
    mount_type = factory.SubFactory(MountTypeFactory)
    road_name = None
    lane_number = None
    lane_type = None
    location_specifier = None
    validity_period_start = None
    validity_period_end = None
    seasonal_validity_period_start = None
    seasonal_validity_period_end = None
    owner = factory.SubFactory(OwnerFactory)
    responsible_entity = None
    parent = factory.SubFactory(TrafficSignRealFactory)
    additional_sign_plan = None
    mount_real = factory.SubFactory(MountRealFactory)
    installation_id = factory.sequence(lambda n: f"installation_id{n}")
    installation_details = "Installaation details"
    installed_by = None
    manufacturer = factory.sequence(lambda n: f"Manufacturer{n}")
    rfid = factory.sequence(lambda n: f"rfid{n}")
    legacy_code = "TestLegacyCode"
    permit_decision_id = factory.sequence(lambda n: f"permit_decision{n}")
    operation = None
    scanned_at = None
    attachment_url = factory.sequence(lambda n: f"attachment_url{n}")
    coverage_area = None


def get_additional_sign_real(
    location=test_point_3d,
    device_type=None,
    parent=None,
    mount_real=None,
    additional_sign_plan=None,
    owner=None,
    content_s=None,
    missing_content=False,
    order=None,
    responsible_entity=None,
) -> AdditionalSignReal:
    user = get_user("test_user")
    owner = owner or get_owner()

    kwargs = {}
    if order is not None:
        kwargs["order"] = order

    asr = AdditionalSignReal.objects.get_or_create(
        parent=parent,
        mount_real=mount_real,
        additional_sign_plan=additional_sign_plan,
        location=location,
        device_type=device_type,
        owner=owner,
        responsible_entity=responsible_entity,
        created_by=user,
        updated_by=user,
        content_s=content_s,
        missing_content=missing_content,
        **kwargs,
    )[0]
    asr.refresh_from_db()
    return asr


def get_api_client(user=None, use_token_auth=False):
    api_client = APIClient()
    api_client.default_format = "json"
    if user and not use_token_auth:
        api_client.force_authenticate(user=user)
    if user and use_token_auth:
        token = Token.objects.create(user=user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


def get_operation_type(name="Test operation type") -> OperationType:
    return OperationType.objects.get_or_create(
        name=name,
        defaults={
            "traffic_sign": True,
            "additional_sign": True,
            "road_marking": True,
            "barrier": True,
            "signpost": True,
            "traffic_light": True,
            "mount": True,
            "furniture_signpost": True,
        },
    )[0]


def add_additional_sign_real_operation(
    additional_sign_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return AdditionalSignRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        additional_sign_real=additional_sign_real,
        created_by=user,
        updated_by=user,
    )


def add_traffic_sign_real_operation(
    traffic_sign_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return TrafficSignRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        traffic_sign_real=traffic_sign_real,
        created_by=user,
        updated_by=user,
    )


def add_road_marking_real_operation(
    road_marking_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return RoadMarkingRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        road_marking_real=road_marking_real,
        created_by=user,
        updated_by=user,
    )


def add_signpost_real_operation(
    signpost_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return SignpostRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        signpost_real=signpost_real,
        created_by=user,
        updated_by=user,
    )


def add_barrier_real_operation(
    barrier_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return BarrierRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        barrier_real=barrier_real,
        created_by=user,
        updated_by=user,
    )


def add_mount_real_operation(
    mount_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return MountRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        mount_real=mount_real,
        created_by=user,
        updated_by=user,
    )


def add_traffic_light_real_operation(
    traffic_light_real,
    operation_type=None,
    operation_date=None,
):
    if not operation_type:
        operation_type = get_operation_type()
    if not operation_date:
        operation_date = datetime.date.today()
    user = get_user("test_user")
    return TrafficLightRealOperation.objects.create(
        operation_type=operation_type,
        operation_date=operation_date,
        traffic_light_real=traffic_light_real,
        created_by=user,
        updated_by=user,
    )


def get_responsible_entity_division(name="DIVISION") -> ResponsibleEntity:
    return ResponsibleEntity.objects.get_or_create(
        name=name,
        defaults=dict(organization_level=OrganizationLevel.DIVISION),
    )[0]


def get_responsible_entity_service(name="SERVICE") -> ResponsibleEntity:
    parent = get_responsible_entity_division()
    return ResponsibleEntity.objects.get_or_create(
        name=name,
        defaults=dict(parent=parent, organization_level=OrganizationLevel.SERVICE),
    )[0]


def get_responsible_entity_unit(name="UNIT") -> ResponsibleEntity:
    parent = get_responsible_entity_service()
    return ResponsibleEntity.objects.get_or_create(
        name=name,
        defaults=dict(parent=parent, organization_level=OrganizationLevel.UNIT),
    )[0]


def get_responsible_entity_project(name="PROJECT") -> ResponsibleEntity:
    parent = get_responsible_entity_unit()
    return ResponsibleEntity.objects.get_or_create(
        name=name,
        defaults=dict(parent=parent, organization_level=OrganizationLevel.PROJECT),
    )[0]
