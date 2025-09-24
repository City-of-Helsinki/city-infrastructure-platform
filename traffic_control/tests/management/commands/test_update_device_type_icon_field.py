from tempfile import TemporaryDirectory

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from traffic_control.models.common import TrafficControlDeviceType, TrafficControlDeviceTypeIcon

# --- FIXTURE: Mock Storage and Create Icons ---


@pytest.fixture
def mock_storage_and_icons(db, settings):
    """
    Uses TemporaryDirectory to mock the file storage to ensure side-effect-generated
    files are cleaned up after the test. Returns the successful icon object.
    """
    with TemporaryDirectory() as tmp_dir:
        settings.MEDIA_ROOT = tmp_dir
        icon_file = SimpleUploadedFile(
            name="icons/matching_icon.svg", content=b"<svg></svg>", content_type="image/svg+xml"
        )
        existing_icon = TrafficControlDeviceTypeIcon.objects.create(file=icon_file)
        yield existing_icon


# --- FIXTURE: Set up TrafficControlDeviceType objects ---


@pytest.fixture
def setup_device_types(db, mock_storage_and_icons):
    """Sets up device types covering the required test cases."""

    existing_icon = mock_storage_and_icons

    # CASE 1: Icon text exists AND matching file exists (SUCCESS case)
    device_type_success = TrafficControlDeviceType.objects.create(
        code="SUCCESS",
        icon="matching_icon.svg",
        icon_file=None,  # Ensure it starts as None
    )

    # CASE 2: No icon text (SKIPPED case)
    device_type_no_icon = TrafficControlDeviceType.objects.create(
        code="NO_ICON",
        icon="",  # Empty string icon
        icon_file=None,
    )

    # CASE 3: Icon text exists, but no file matches it (BOGUS/WARNING case)
    device_type_missing_icon = TrafficControlDeviceType.objects.create(
        code="MISSING_ICON",
        icon="nonexistent.svg",
        icon_file=None,
    )

    # CASE 4: Icon text exists but is not .svg (BOGUS/WARNING case)
    device_type_bogus_extension = TrafficControlDeviceType.objects.create(
        code="BOGUS_EXT",
        icon="icon.png",  # Does not end with .svg
        icon_file=None,
    )

    return {
        "success": device_type_success.pk,
        "no_icon": device_type_no_icon.pk,
        "missing_icon": device_type_missing_icon.pk,
        "bogus_ext": device_type_bogus_extension.pk,
        "matching_icon_object": existing_icon,
    }


@pytest.mark.django_db
def test_update_device_type_icon_field_command(setup_device_types, capsys):
    call_command("update_device_type_icon_field")
    captured = capsys.readouterr()

    # Non-error situations produce reasonable output
    assert "Updating TrafficControlDeviceType icon_file fields..." in captured.out
    assert "Skipped TrafficControlDeviceType without icon string. Device type: NO_ICON" in captured.out
    assert "Updated 1 TrafficControlDeviceType objects." in captured.out

    # Error situations produce reasonable output
    assert "TrafficControlDeviceTypeIcon 'nonexistent.svg' not found. Device type: MISSING_ICON" in captured.err
    assert "2 TrafficControlDeviceType could not be updated" in captured.err
    assert "\tIcon: 'nonexistent.svg'. Device type: MISSING_ICON" in captured.err
    assert "\tIcon: 'icon.png'. Device type: BOGUS_EXT" in captured.err

    # Get the updated objects from the database
    updated_success_dt = TrafficControlDeviceType.objects.get(pk=setup_device_types["success"])
    no_icon_dt = TrafficControlDeviceType.objects.get(pk=setup_device_types["no_icon"])
    missing_icon_dt = TrafficControlDeviceType.objects.get(pk=setup_device_types["missing_icon"])
    bogus_ext_dt = TrafficControlDeviceType.objects.get(pk=setup_device_types["bogus_ext"])
    expected_icon = setup_device_types["matching_icon_object"]

    # SUCCESS CASE: icon_file MUST be set to the matching icon object
    assert updated_success_dt.icon_file == expected_icon

    # NO ICON CASE: icon_file MUST remain None (unchanged)
    assert no_icon_dt.icon_file is None

    # MISSING ICON CASE: icon_file MUST remain None (unchanged)
    assert missing_icon_dt.icon_file is None

    # BOGUS EXTENSION CASE: icon_file MUST remain None (unchanged)
    assert bogus_ext_dt.icon_file is None
