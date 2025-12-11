from io import StringIO

import pytest
from django.core.management import call_command

from city_furniture.models.common import CityFurnitureDeviceType


@pytest.mark.django_db
def test_creates_dummy_device_type_when_not_exists():
    """Test that the command creates a dummy device type if it doesn't exist."""
    assert not CityFurnitureDeviceType.objects.filter(code="DummyDT").exists()

    call_command("create_dummy_city_furniture_device_type")

    assert CityFurnitureDeviceType.objects.filter(code="DummyDT").exists()
    dummy_dt = CityFurnitureDeviceType.objects.get(code="DummyDT")
    assert dummy_dt.target_model is None
    assert dummy_dt.description_en == "Placeholder for devices that have None set to device_type"
    assert dummy_dt.description_fi == "Paikanpitäjä laitteille, joilla ei ole device_type asetettu"


@pytest.mark.django_db
def test_does_not_duplicate_dummy_device_type():
    """Test that running the command twice doesn't create duplicates."""
    call_command("create_dummy_city_furniture_device_type")
    first_count = CityFurnitureDeviceType.objects.filter(code="DummyDT").count()

    call_command("create_dummy_city_furniture_device_type")
    second_count = CityFurnitureDeviceType.objects.filter(code="DummyDT").count()

    assert first_count == 1
    assert second_count == 1


@pytest.mark.django_db
def test_dry_run_does_not_create_device_type():
    """Test that dry-run mode doesn't create the device type."""
    call_command("create_dummy_city_furniture_device_type", "--dry-run")

    assert not CityFurnitureDeviceType.objects.filter(code="DummyDT").exists()


@pytest.mark.django_db
def test_no_updates_when_no_null_device_types():
    """
    Test command output when there are no objects with null device_type.
    Note: device_type is required in city_furniture models, so this should always be the case.
    """
    out = StringIO()
    call_command("create_dummy_city_furniture_device_type", stdout=out)

    output = out.getvalue()
    # Should create the dummy device type but find no objects to update
    assert "No city furniture devices with device_type=None found" in output


@pytest.mark.django_db
def test_models_parameter_accepted():
    """Test that --models parameter is accepted."""
    out = StringIO()
    call_command("create_dummy_city_furniture_device_type", "--models", "FurnitureSignpostPlan", stdout=out)

    output = out.getvalue()
    assert "Processing only selected models" in output or "No city furniture devices" in output


@pytest.mark.django_db
def test_models_parameter_with_multiple_models():
    """Test that --models parameter works with multiple model names."""
    out = StringIO()
    call_command(
        "create_dummy_city_furniture_device_type",
        "--models",
        "FurnitureSignpostPlan",
        "FurnitureSignpostReal",
        stdout=out,
    )

    output = out.getvalue()
    # Should process the command successfully
    assert "Processing only selected models" in output or "No city furniture devices" in output


@pytest.mark.django_db
def test_list_ids_parameter_accepted():
    """Test that --list-ids parameter is accepted."""
    out = StringIO()
    call_command("create_dummy_city_furniture_device_type", "--list-ids", stdout=out)

    output = out.getvalue()
    # Command should complete successfully
    assert "No city furniture devices with device_type=None found" in output


@pytest.mark.django_db
def test_dry_run_with_list_ids():
    """Test that --list-ids works with --dry-run."""
    out = StringIO()
    call_command("create_dummy_city_furniture_device_type", "--dry-run", "--list-ids", stdout=out)

    output = out.getvalue()
    assert "DRY RUN MODE" in output


@pytest.mark.django_db
def test_combined_parameters():
    """Test using multiple parameters together."""
    out = StringIO()
    call_command(
        "create_dummy_city_furniture_device_type",
        "--dry-run",
        "--models",
        "FurnitureSignpostPlan",
        "--list-ids",
        stdout=out,
    )

    output = out.getvalue()
    assert "DRY RUN MODE" in output
    assert "Processing only selected models" in output


@pytest.mark.django_db
def test_command_creates_device_type_with_valid_enums():
    """Test that the created device type has valid enum values."""
    call_command("create_dummy_city_furniture_device_type")

    dummy_dt = CityFurnitureDeviceType.objects.get(code="DummyDT")
    # Verify the enum values are valid (1030 = OTHERS, 1090 = FREE_STANDING_SIGN)
    assert dummy_dt.class_type == 1030
    assert dummy_dt.function_type == 1090
