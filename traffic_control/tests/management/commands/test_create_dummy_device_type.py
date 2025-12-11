from io import StringIO

import pytest
from django.core.management import call_command

from traffic_control.models import TrafficControlDeviceType
from traffic_control.tests.factories import (
    AdditionalSignPlanFactory,
    AdditionalSignRealFactory,
    BarrierPlanFactory,
    BarrierRealFactory,
    RoadMarkingPlanFactory,
    RoadMarkingRealFactory,
    SignpostPlanFactory,
    SignpostRealFactory,
    TrafficControlDeviceTypeFactory,
    TrafficLightPlanFactory,
    TrafficLightRealFactory,
    TrafficSignPlanFactory,
    TrafficSignRealFactory,
)


@pytest.mark.django_db
def test_creates_dummy_device_type_when_not_exists():
    """Test that the command creates a dummy device type if it doesn't exist."""
    assert not TrafficControlDeviceType.objects.filter(code="DummyDT").exists()

    call_command("create_dummy_device_type")

    assert TrafficControlDeviceType.objects.filter(code="DummyDT").exists()
    dummy_dt = TrafficControlDeviceType.objects.get(code="DummyDT")
    assert dummy_dt.target_model is None
    assert dummy_dt.description == "Placeholder for devices that have None set to device_type"


@pytest.mark.django_db
def test_does_not_duplicate_dummy_device_type():
    """Test that running the command twice doesn't create duplicates."""
    call_command("create_dummy_device_type")
    first_count = TrafficControlDeviceType.objects.filter(code="DummyDT").count()

    call_command("create_dummy_device_type")
    second_count = TrafficControlDeviceType.objects.filter(code="DummyDT").count()

    assert first_count == 1
    assert second_count == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    [
        AdditionalSignPlanFactory,
        AdditionalSignRealFactory,
        BarrierPlanFactory,
        BarrierRealFactory,
        RoadMarkingPlanFactory,
        RoadMarkingRealFactory,
        SignpostPlanFactory,
        SignpostRealFactory,
        TrafficLightPlanFactory,
        TrafficLightRealFactory,
        TrafficSignPlanFactory,
        TrafficSignRealFactory,
    ],
)
def test_updates_model_with_null_device_type(factory):
    """Test that objects with null device_type are updated."""
    obj_without_dt = factory(device_type=None)

    call_command("create_dummy_device_type")

    obj_without_dt.refresh_from_db()
    assert obj_without_dt.device_type.code == "DummyDT"


@pytest.mark.django_db
def test_updates_traffic_sign_plan_with_null_device_type():
    """Test that TrafficSignPlan objects with null device_type are updated but not existing ones."""
    sign_with_dt = TrafficSignPlanFactory()
    sign_without_dt = TrafficSignPlanFactory(device_type=None)

    call_command("create_dummy_device_type")

    sign_with_dt.refresh_from_db()
    sign_without_dt.refresh_from_db()

    assert sign_with_dt.device_type.code != "DummyDT"
    assert sign_without_dt.device_type.code == "DummyDT"


@pytest.mark.django_db
def test_updates_multiple_models_at_once():
    """Test that the command updates multiple model types in one run."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)
    barrier_without_dt = BarrierPlanFactory(device_type=None)
    marking_without_dt = RoadMarkingRealFactory(device_type=None)

    call_command("create_dummy_device_type")

    sign_without_dt.refresh_from_db()
    barrier_without_dt.refresh_from_db()
    marking_without_dt.refresh_from_db()

    assert sign_without_dt.device_type.code == "DummyDT"
    assert barrier_without_dt.device_type.code == "DummyDT"
    assert marking_without_dt.device_type.code == "DummyDT"


@pytest.mark.django_db
def test_dry_run_does_not_create_device_type():
    """Test that dry-run mode doesn't create the device type."""
    call_command("create_dummy_device_type", "--dry-run")

    assert not TrafficControlDeviceType.objects.filter(code="DummyDT").exists()


@pytest.mark.django_db
def test_dry_run_does_not_update_objects():
    """Test that dry-run mode doesn't update objects."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)

    call_command("create_dummy_device_type", "--dry-run")

    sign_without_dt.refresh_from_db()
    assert sign_without_dt.device_type is None


@pytest.mark.django_db
def test_models_parameter_filters_updates():
    """Test that --models parameter only updates specified models."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)
    barrier_without_dt = BarrierPlanFactory(device_type=None)

    call_command("create_dummy_device_type", "--models", "TrafficSignPlan")

    sign_without_dt.refresh_from_db()
    barrier_without_dt.refresh_from_db()

    assert sign_without_dt.device_type.code == "DummyDT"
    assert barrier_without_dt.device_type is None


@pytest.mark.django_db
def test_models_parameter_with_multiple_models():
    """Test that --models parameter works with multiple model names."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)
    barrier_without_dt = BarrierPlanFactory(device_type=None)
    marking_without_dt = RoadMarkingRealFactory(device_type=None)

    call_command("create_dummy_device_type", "--models", "TrafficSignPlan", "BarrierPlan")

    sign_without_dt.refresh_from_db()
    barrier_without_dt.refresh_from_db()
    marking_without_dt.refresh_from_db()

    assert sign_without_dt.device_type.code == "DummyDT"
    assert barrier_without_dt.device_type.code == "DummyDT"
    assert marking_without_dt.device_type is None


@pytest.mark.django_db
def test_list_ids_shows_updated_ids():
    """Test that --list-ids parameter displays the IDs of updated objects."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)

    out = StringIO()
    call_command("create_dummy_device_type", "--list-ids", stdout=out)

    output = out.getvalue()
    assert str(sign_without_dt.id) in output
    assert "Updated IDs:" in output


@pytest.mark.django_db
def test_list_ids_with_dry_run():
    """Test that --list-ids works with --dry-run."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)

    out = StringIO()
    call_command("create_dummy_device_type", "--dry-run", "--list-ids", stdout=out)

    output = out.getvalue()
    assert str(sign_without_dt.id) in output
    assert "IDs that would be updated:" in output


@pytest.mark.django_db
def test_output_shows_update_count():
    """Test that command output shows the number of updated records."""
    TrafficSignPlanFactory(device_type=None)
    TrafficSignPlanFactory(device_type=None)
    BarrierPlanFactory(device_type=None)

    out = StringIO()
    call_command("create_dummy_device_type", stdout=out)

    output = out.getvalue()
    assert "2 TrafficSignPlan" in output
    assert "1 BarrierPlan" in output
    assert "Total:" in output


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


@pytest.mark.django_db
def test_combined_parameters():
    """Test using multiple parameters together."""
    sign_without_dt = TrafficSignPlanFactory(device_type=None)
    barrier_without_dt = BarrierPlanFactory(device_type=None)

    out = StringIO()
    call_command("create_dummy_device_type", "--dry-run", "--models", "TrafficSignPlan", "--list-ids", stdout=out)

    output = out.getvalue()
    assert "DRY RUN MODE" in output
    assert "Processing only selected models" in output
    assert str(sign_without_dt.id) in output

    # Verify nothing was actually updated
    sign_without_dt.refresh_from_db()
    barrier_without_dt.refresh_from_db()
    assert sign_without_dt.device_type is None
    assert barrier_without_dt.device_type is None
