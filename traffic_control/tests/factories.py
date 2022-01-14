import datetime
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle
from traffic_control.models import (
    AdditionalSignContentPlan,
    AdditionalSignContentReal,
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
    Owner,
    Plan,
    Reflective,
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
from traffic_control.models.common import OperationType
from traffic_control.tests.test_base_api import test_multi_polygon, test_point, test_polygon
from traffic_control.tests.test_base_api_3d import test_point_3d


def get_user(username=None, admin=False):
    if not username:
        username = get_random_string()  # pragma: no cover
    return get_user_model().objects.get_or_create(
        username=username,
        password="x",
        first_name="John",
        last_name="Doe",
        email="test@example.com",
        is_staff=admin,
        is_superuser=admin,
    )[0]


def get_operational_area(area=None):
    return OperationalArea.objects.get_or_create(
        name="Test operational area",
        location=area or MultiPolygon(test_polygon, srid=settings.SRID),
    )[0]


def get_owner(name_fi="Omistaja", name_en="Owner"):
    return Owner.objects.get_or_create(name_fi=name_fi, name_en=name_en)[0]


def get_plan(location=test_multi_polygon, name="Test plan"):
    user = get_user("test_user")
    superuser = get_user("super user", admin=True)
    return Plan.objects.get_or_create(
        name=name,
        plan_number="2020_1",
        location=location,
        planner=user,
        decision_maker=superuser,
        created_by=user,
        updated_by=user,
    )[0]


def get_barrier_plan(location="", plan=None, device_type=None):
    user = get_user("test_user")
    return BarrierPlan.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
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


def get_barrier_real(location="", device_type=None):
    user = get_user("test_user")

    return BarrierReal.objects.create(
        device_type=device_type or get_traffic_control_device_type(),
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


def get_mount_type(code="POST", description="Post"):
    return MountType.objects.get_or_create(code=code, description=description)[0]


def get_mount_plan(location="", plan=None):
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


def get_mount_real(location=""):
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


def get_road_marking_plan(location="", plan=None, device_type=None):
    user = get_user("test_user")

    return RoadMarkingPlan.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
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
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_real(location="", device_type=None):
    user = get_user("test_user")

    return RoadMarkingReal.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        road_marking_plan=get_road_marking_plan(),
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
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_plan(location="", plan=None, device_type=None):
    user = get_user("test_user")

    return SignpostPlan.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        location=location or test_point,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_real(location="", device_type=None):
    user = get_user("test_user")

    return SignpostReal.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        signpost_plan=get_signpost_plan(),
        location=location or test_point,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_plan(location="", plan=None, device_type=None):
    user = get_user("test_user")

    return TrafficLightPlan.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        location=location or test_point,
        type=TrafficLightType.SIGNAL,
        lifecycle=Lifecycle.ACTIVE,
        mount_type=get_mount_type(),
        road_name="Testingroad",
        sound_beacon=TrafficLightSoundBeaconValue.YES,
        plan=plan,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_real(location="", device_type=None):
    user = get_user("test_user")

    return TrafficLightReal.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        traffic_light_plan=get_traffic_light_plan(),
        location=location or test_point,
        type=TrafficLightType.SIGNAL,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        mount_type=get_mount_type(),
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
):
    return TrafficControlDeviceType.objects.get_or_create(
        code=code,
        description=description,
        target_model=target_model,
        value=value,
    )[0]


def get_traffic_sign_plan(location="", plan=None, device_type=None):
    user = get_user("test_user")

    return TrafficSignPlan.objects.get_or_create(
        device_type=device_type or get_traffic_control_device_type(),
        location=location or test_point_3d,
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_sign_real(location="", device_type=None):
    user = get_user("test_user")

    if not device_type:
        device_type = get_traffic_control_device_type()

    return TrafficSignReal.objects.get_or_create(
        traffic_sign_plan=get_traffic_sign_plan(device_type=device_type),
        device_type=device_type,
        location=location or test_point_3d,
        installation_date=datetime.date(2020, 1, 1),
        lifecycle=Lifecycle.ACTIVE,
        owner=get_owner(),
        created_by=user,
        updated_by=user,
    )[0]


def get_additional_sign_plan(location=test_point_3d, parent=None, owner=None, plan=None):
    user = get_user("test_user")
    owner = owner or get_owner()

    return AdditionalSignPlan.objects.get_or_create(
        parent=parent or get_traffic_sign_plan(),
        location=location,
        owner=owner,
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_additional_sign_real(location=test_point_3d, parent=None, owner=None):
    user = get_user("test_user")
    owner = owner or get_owner()

    return AdditionalSignReal.objects.get_or_create(
        parent=parent or get_traffic_sign_real(),
        location=location,
        owner=owner,
        created_by=user,
        updated_by=user,
    )[0]


def get_additional_sign_content_plan(parent=None, device_type=None, order=1):
    user = get_user("test_user")

    if not device_type:
        device_type = get_traffic_control_device_type()

    return AdditionalSignContentPlan.objects.get_or_create(
        parent=parent or get_additional_sign_plan(),
        order=order,
        text="Content",
        device_type=device_type,
        created_by=user,
        updated_by=user,
    )[0]


def get_additional_sign_content_real(parent=None, device_type=None, order=1):
    user = get_user("test_user")

    if not device_type:
        device_type = get_traffic_control_device_type()

    return AdditionalSignContentReal.objects.get_or_create(
        parent=parent or get_additional_sign_real(),
        order=order,
        text="Content",
        device_type=device_type,
        created_by=user,
        updated_by=user,
    )[0]


def get_api_client(user=None):
    api_client = APIClient()
    api_client.default_format = "json"
    if user:
        api_client.force_authenticate(user=user)
    return api_client


def get_operation_type(name="Test operation type"):
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
