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
    Reflective,
    TrafficSignCode,
    TrafficSignPlan,
    TrafficSignReal,
)
from traffic_control.tests.test_base_api import test_point


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


def get_barrier_plan(location=""):
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


def get_mount_plan(location=""):
    user = get_user("test_user")

    return MountPlan.objects.get_or_create(
        type=MountType.PORTAL,
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
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


def get_traffic_sign_code():
    return TrafficSignCode.objects.get_or_create(code="A11", description="Test")[0]


def get_traffic_sign_plan(location=""):
    user = get_user("test_user")

    return TrafficSignPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        location=location or test_point,
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
        lifecycle=Lifecycle.ACTIVE,
        created_by=user,
        updated_by=user,
    )[0]


def get_traffic_sign_real(location=""):
    user = get_user("test_user")

    return TrafficSignReal.objects.get_or_create(
        traffic_sign_plan=get_traffic_sign_plan(),
        code=get_traffic_sign_code(),
        location=location or test_point,
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
