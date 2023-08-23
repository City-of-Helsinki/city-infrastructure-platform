import datetime
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon
from django.db.models import Value
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle, OrganizationLevel
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
from traffic_control.tests.test_base_api import test_multi_polygon, test_point, test_polygon
from traffic_control.tests.test_base_api_3d import test_point_3d
from users.models import User


def get_user(username=None, admin=False, bypass_operational_area=False, bypass_responsible_entity=False) -> User:
    if not username:
        username = get_random_string(length=12)  # pragma: no cover
    return get_user_model().objects.get_or_create(
        username=username,
        password="x",
        first_name="John",
        last_name="Doe",
        email="test@example.com",
        is_staff=admin,
        is_superuser=admin,
        bypass_responsible_entity=bypass_responsible_entity,
        bypass_operational_area=bypass_operational_area,
    )[0]


def get_operational_area(area=None, name=None) -> OperationalArea:
    return OperationalArea.objects.get_or_create(
        name=name or "Test operational area",
        location=area or MultiPolygon(test_polygon, srid=settings.SRID),
    )[0]


def get_owner(name_fi="Omistaja", name_en="Owner") -> Owner:
    return Owner.objects.get_or_create(name_fi=name_fi, name_en=name_en)[0]


def get_plan(location=test_multi_polygon, name="Test plan", derive_location=False) -> Plan:
    user = get_user("test_user")
    return Plan.objects.get_or_create(
        name=name,
        plan_number="2020_1",
        location=location,
        derive_location=derive_location,
        created_by=user,
        updated_by=user,
    )[0]


def get_barrier_plan(location="", plan=None, device_type=None) -> BarrierPlan:
    user = get_user("test_user")
    return BarrierPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        plan=plan,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_barrier_real(location="", device_type=None) -> BarrierReal:
    user = get_user("test_user")

    return BarrierReal.objects.create(
        device_type=device_type,
        barrier_plan=get_barrier_plan(),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 20),
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )


def get_mount_type(code="POST", description="Post") -> MountType:
    return MountType.objects.get_or_create(code=code, description=description)[0]


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


def get_mount_plan(location="", plan=None) -> MountPlan:
    user = get_user("test_user")

    return MountPlan.objects.get_or_create(
        mount_type=get_mount_type(code="PORTAL", description="Portal"),
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_mount_real(location="") -> MountReal:
    user = get_user("test_user")

    return MountReal.objects.get_or_create(
        mount_plan=get_mount_plan(),
        mount_type=get_mount_type(code="PORTAL", description="Portal"),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_plan(
    location="",
    plan=None,
    device_type=None,
    traffic_sign_plan=None,
) -> RoadMarkingPlan:
    user = get_user("test_user")

    return RoadMarkingPlan.objects.get_or_create(
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
        traffic_sign_plan=traffic_sign_plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_real(
    location="",
    device_type=None,
    road_marking_plan=None,
    traffic_sign_real=None,
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
) -> SignpostPlan:
    user = get_user("test_user")

    return SignpostPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        parent=parent,
        mount_plan=mount_plan,
        txt=txt,
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_real(
    location="",
    device_type=None,
    signpost_plan=None,
    parent=None,
    mount_real=None,
    txt=None,
) -> SignpostReal:
    user = get_user("test_user")

    return SignpostReal.objects.get_or_create(
        device_type=device_type,
        signpost_plan=signpost_plan or get_signpost_plan(),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
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
) -> TrafficLightPlan:
    user = get_user("test_user")

    return TrafficLightPlan.objects.get_or_create(
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
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_real(
    location="",
    device_type=None,
    traffic_light_plan=None,
    mount_real=None,
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
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_control_device_type(
    code: str = "A11",
    description: str = "Test",
    target_model: Optional[DeviceTypeTargetModel] = None,
    value: str = "",
    content_schema: Optional[Any] = None,
) -> TrafficControlDeviceType:
    if content_schema is None:
        # Distinguish between JSON null and SQL NULL
        content_schema = Value("null")

    dt = TrafficControlDeviceType.objects.get_or_create(
        code=code,
        description=description,
        target_model=target_model,
        value=value,
        content_schema=content_schema,
    )[0]
    dt.refresh_from_db()
    return dt


def get_traffic_sign_plan(
    location="",
    plan=None,
    device_type=None,
    mount_plan=None,
) -> TrafficSignPlan:
    user = get_user("test_user")

    return TrafficSignPlan.objects.get_or_create(
        device_type=device_type,
        location=location or test_point_3d,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        mount_plan=mount_plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_sign_real(
    location="",
    device_type=None,
    traffic_sign_plan=None,
    mount_real=None,
) -> TrafficSignReal:
    user = get_user("test_user")

    return TrafficSignReal.objects.get_or_create(
        traffic_sign_plan=traffic_sign_plan or get_traffic_sign_plan(),
        device_type=device_type,
        location=location or test_point_3d,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
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
    order=None,
) -> AdditionalSignPlan:
    user = get_user("test_user")
    owner = owner or get_owner()

    if content_s is None:
        # Distinguish between JSON null and SQL NULL
        content_s = Value("null")

    kwargs = {}
    if order is not None:
        kwargs["order"] = order

    asp = AdditionalSignPlan.objects.get_or_create(
        parent=parent,
        mount_plan=mount_plan,
        location=location,
        device_type=device_type,
        owner=owner,
        plan=plan,
        created_by=user,
        updated_by=user,
        content_s=content_s,
        **kwargs,
    )[0]
    asp.refresh_from_db()
    return asp


def get_additional_sign_real(
    location=test_point_3d,
    device_type=None,
    parent=None,
    mount_real=None,
    additional_sign_plan=None,
    owner=None,
    content_s=None,
    order=None,
) -> AdditionalSignReal:
    user = get_user("test_user")
    owner = owner or get_owner()

    if content_s is None:
        # Distinguish between JSON null and SQL NULL
        content_s = Value("null")

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
        created_by=user,
        updated_by=user,
        content_s=content_s,
        **kwargs,
    )[0]
    asr.refresh_from_db()
    return asr


def get_api_client(user=None):
    api_client = APIClient()
    api_client.default_format = "json"
    if user:
        api_client.force_authenticate(user=user)
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
