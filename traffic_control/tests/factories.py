from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient

from traffic_control.models import Lifecycle, TrafficSignCode, TrafficSignPlan


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


def get_traffic_sign_code():
    return TrafficSignCode.objects.get_or_create(code="A11", description="Test")[0]


def get_traffic_sign(location=""):
    user = get_user("test_user")
    return TrafficSignPlan.objects.get_or_create(
        code=get_traffic_sign_code(),
        location=location or Point(10.0, 10.0, srid=settings.SRID),
        decision_date=datetime.strptime("01012020", "%d%m%Y").date(),
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
