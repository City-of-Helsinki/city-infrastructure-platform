"""Tests for the traffic sign value check run info admin."""
import pytest
from django.urls import reverse
from django.utils import timezone

from traffic_control.models import TrafficSignValueCheckRunInfo

CHANGELIST_URL = reverse("admin:traffic_control_trafficsignvaluecheckruninfo_changelist")


@pytest.fixture
def run_info(db):
    """Create a run info with one recorded problem."""
    return TrafficSignValueCheckRunInfo.objects.create(
        start_time=timezone.now(),
        end_time=timezone.now(),
        checked_codes=["C21", "C21_3"],
        problems=[{"id": "abc", "device_type_code": "C21_3", "expected_value": "2.1"}],
        checked_count=2,
        problem_count=1,
    )


@pytest.mark.django_db
def test_changelist_is_available(admin_client, run_info):
    response = admin_client.get(CHANGELIST_URL)

    assert response.status_code == 200


@pytest.mark.django_db
def test_change_view_is_available_as_read_only(admin_client, run_info):
    url = reverse("admin:traffic_control_trafficsignvaluecheckruninfo_change", args=[run_info.pk])

    response = admin_client.get(url, follow=True)

    assert response.status_code == 200


@pytest.mark.django_db
def test_adding_is_denied(admin_client):
    url = reverse("admin:traffic_control_trafficsignvaluecheckruninfo_add")

    response = admin_client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_changing_is_denied(admin_client, run_info):
    url = reverse("admin:traffic_control_trafficsignvaluecheckruninfo_change", args=[run_info.pk])

    response = admin_client.post(url, {"checked_count": 99})

    run_info.refresh_from_db()
    assert response.status_code in (302, 403)
    assert run_info.checked_count == 2
