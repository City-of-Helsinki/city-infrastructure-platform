from io import StringIO

import pytest
from django.core.management import call_command

from traffic_control.models import TrafficControlDeviceType
from traffic_control.tests.factories import (
    BarrierPlanFactory,
    TrafficControlDeviceTypeFactory,
    TrafficSignPlanFactory,
)


@pytest.mark.django_db
def test_creates_dummy_device_type_when_not_exists():
    """Test that the command creates a dummy device type if it doesn't exist."""
    # Delete DummyDT if it exists from migrations
    TrafficControlDeviceType.objects.filter(code="DummyDT").delete()

    assert not TrafficControlDeviceType.objects.filter(code="DummyDT").exists()

    call_command("create_dummy_device_type")

    assert TrafficControlDeviceType.objects.filter(code="DummyDT").exists()
    dummy_dt = TrafficControlDeviceType.objects.get(code="DummyDT")
    assert dummy_dt.target_model is None
    assert dummy_dt.description == "Placeholder for devices that have None set to device_type"


@pytest.mark.django_db
def test_does_not_duplicate_dummy_device_type():
    """Test that running the command twice doesn't create duplicates."""
    # Delete DummyDT if it exists from migrations
    TrafficControlDeviceType.objects.filter(code="DummyDT").delete()

    call_command("create_dummy_device_type")
    first_count = TrafficControlDeviceType.objects.filter(code="DummyDT").count()

    call_command("create_dummy_device_type")
    second_count = TrafficControlDeviceType.objects.filter(code="DummyDT").count()

    assert first_count == 1
    assert second_count == 1


@pytest.mark.django_db
def test_dry_run_does_not_create_device_type():
    """Test that dry-run mode doesn't create the device type."""
    # Delete DummyDT if it exists from migrations
    TrafficControlDeviceType.objects.filter(code="DummyDT").delete()

    call_command("create_dummy_device_type", "--dry-run")

    assert not TrafficControlDeviceType.objects.filter(code="DummyDT").exists()


@pytest.mark.django_db
def test_no_updates_when_no_null_device_types():
    """Test command output when there are no objects with null device_type."""
    # Explicitly create a device_type to ensure it's not None
    device_type = TrafficControlDeviceTypeFactory()
    TrafficSignPlanFactory(device_type=device_type)
    BarrierPlanFactory(device_type=device_type)

    out = StringIO()
    call_command("create_dummy_device_type", stdout=out)

    output = out.getvalue()
    assert "No devices with device_type=None found" in output
