from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from traffic_control.models import (
    BarrierPlan,
    BarrierReal,
    ConnectionType,
    Lifecycle,
    MountPlan,
    MountReal,
    MountType,
    Plan,
    Reflective,
    RoadMarkingColor,
    RoadMarkingPlan,
    RoadMarkingReal,
    SignpostPlan,
    SignpostReal,
    TrafficLightPlan,
    TrafficLightReal,
    TrafficLightSoundBeaconValue,
    TrafficLightType,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.tests.test_base_api import test_multi_polygon, test_point
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


def get_plan(location=""):
    user = get_user("test_user")
    superuser = get_user("super user", admin=True)
    return Plan.objects.get_or_create(
        name="Test plan",
        plan_number="2020_1",
        location=location or test_multi_polygon,
        planner=user,
        decision_maker=superuser,
        created_by=user,
        updated_by=user,
    )[0]


def get_barrier_plan(location="", plan=None):
    user = get_user("test_user")
    return BarrierPlan.objects.get_or_create(
        type=get_traffic_sign_code(),
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_barrier_real(location=""):
    user = get_user("test_user")

    return BarrierReal.objects.create(
        type=get_traffic_sign_code(),
        barrier_plan=get_barrier_plan(),
        location=location or test_point,
        installation_date=datetime.strptime("20012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        material="Betoni",
        reflective=Reflective.YES,
        connection_type=ConnectionType.OPEN_OUT,
        road_name="Testingroad",
        created_by=user,
        updated_by=user,
    )


def get_mount_plan(location="", plan=None):
    user = get_user("test_user")

    return MountPlan.objects.get_or_create(
        type=MountType.PORTAL,
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_mount_real(location=""):
    user = get_user("test_user")

    return MountReal.objects.get_or_create(
        mount_plan=get_mount_plan(),
        type=MountType.PORTAL,
        location=location or test_point,
        installation_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_plan(location="", plan=None):
    user = get_user("test_user")

    return RoadMarkingPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        value="30",
        color=RoadMarkingColor.WHITE,
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        material="Maali",
        is_grinded=True,
        is_raised=False,
        has_rumble_strips=True,
        road_name="Testingroad",
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_road_marking_real(location=""):
    user = get_user("test_user")

    return RoadMarkingReal.objects.get_or_create(
        code=get_traffic_sign_code(),
        road_marking_plan=get_road_marking_plan(),
        value="30",
        color=RoadMarkingColor.WHITE,
        location=location or test_point,
        installation_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        material="Maali",
        is_grinded=True,
        is_raised=False,
        has_rumble_strips=True,
        road_name="Testingroad",
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_plan(location="", plan=None):
    user = get_user("test_user")

    return SignpostPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_signpost_real(location=""):
    user = get_user("test_user")

    return SignpostReal.objects.get_or_create(
        code=get_traffic_sign_code(),
        signpost_plan=get_signpost_plan(),
        location=location or test_point,
        installation_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_plan(location="", plan=None):
    user = get_user("test_user")

    return TrafficLightPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        location=location or test_point,
        type=TrafficLightType.TRAFFIC_LIGHT,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        mount_type=MountType.POST,
        road_name="Testingroad",
        sound_beacon=TrafficLightSoundBeaconValue.YES,
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_light_real(location=""):
    user = get_user("test_user")

    return TrafficLightReal.objects.get_or_create(
        code=get_traffic_sign_code(),
        traffic_light_plan=get_traffic_light_plan(),
        location=location or test_point,
        type=TrafficLightType.TRAFFIC_LIGHT,
        installation_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        mount_type=MountType.POST,
        road_name="Testingroad",
        sound_beacon=TrafficLightSoundBeaconValue.YES,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_sign_code(code: str = "A11", description: str = "Test"):
    return TrafficSignCode.objects.get_or_create(code=code, description=description)[0]


def get_traffic_sign_plan(location="", plan=None):
    user = get_user("test_user")

    return TrafficSignPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        location=location or test_point_3d,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        plan=plan,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_sign_real(location=""):
    user = get_user("test_user")

    return TrafficSignReal.objects.get_or_create(
        traffic_sign_plan=get_traffic_sign_plan(),
        code=get_traffic_sign_code(),
        location=location or test_point_3d,
        installation_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        created_by=user,
        updated_by=user,
    )[0]


def get_api_client(user=None):
    api_client = APIClient()
    api_client.default_format = "json"
    if user:
        api_client.force_authenticate(user=user)
    return api_client
