import pytest
from django.urls import reverse

from traffic_control.tests import DEVICE_TYPE_COUNT_OFFSET
from traffic_control.tests.factories import get_api_client, TrafficControlDeviceTypeFactory


@pytest.mark.django_db
def test_limit_offset_pagination():
    """
    Test that pagination works as expected for one endpoint. The functionality
    is global for all endpoints and it is completely included in Django Rest
    Framework, so testing one endpoint is enough at the time of writing.

    The point of this test is to detect possible regression caused by by future
    updates.
    """
    api_client = get_api_client()
    tsc_1 = TrafficControlDeviceTypeFactory(code="A1", description="foo")
    tsc_2 = TrafficControlDeviceTypeFactory(code="A2", description="bar")
    tsc_3 = TrafficControlDeviceTypeFactory(code="A3", description="baz")
    tsc_4 = TrafficControlDeviceTypeFactory(code="A4", description="qux")
    tsc_5 = TrafficControlDeviceTypeFactory(code="A5", description="quux")

    response = api_client.get(reverse("v1:trafficcontroldevicetype-list"), {"limit": 2, "offset": 2})

    result_pks = [r["id"] for r in response.data["results"]]
    assert response.data["count"] == 5 + DEVICE_TYPE_COUNT_OFFSET  # DummyDT exists by default
    assert len(result_pks) == 2
    assert str(tsc_3.pk) in result_pks
    assert str(tsc_4.pk) in result_pks
    assert str(tsc_1.pk) not in result_pks
    assert str(tsc_2.pk) not in result_pks
    assert str(tsc_5.pk) not in result_pks
