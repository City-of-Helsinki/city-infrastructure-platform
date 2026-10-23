import pytest
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from traffic_control.models.common import TrafficControlDeviceTypeIcon


@pytest.fixture(autouse=True)
def mock_static_dir(datadir, monkeypatch):
    """
    Sets the static files location to our test datadir.
    """
    # NOTE: needs to be done in this awkward manner due to our command introspecting the static path from the module
    monkeypatch.setattr(apps.get_app_config("traffic_control"), "path", str(datadir))


@pytest.mark.django_db
def test__upload_static_svg_icons_to_blobstorage__command_creates_icons(capsys):
    """
    Verifies that the command correctly creates new TrafficControlDeviceTypeIcon objects for each new file
    """
    # Sanity check, we don't have any icons yet
    assert TrafficControlDeviceTypeIcon.objects.count() == 0

    call_command("upload_static_svg_icons_to_blobstorage")
    captured = capsys.readouterr()

    # Verify final state of the database
    assert TrafficControlDeviceTypeIcon.objects.count() == 3

    # Check for expected output messages
    assert "Icon created" in captured.out
    assert "Icon updated" not in captured.out
    assert "Icon upload to blobstorage complete." in captured.out


@pytest.mark.django_db
def test__upload_static_svg_icons_to_blobstorage__command_creates_and_updates_icons(capsys):
    """
    Verifies that the command correctly creates new TrafficControlDeviceTypeIcon objects for each new file and updates
    existing TrafficControlDeviceTypeIcon objects.
    """
    # Sanity check, we don't have any icons yet
    assert TrafficControlDeviceTypeIcon.objects.count() == 0

    # Create an existing icon that the command should update
    svg_file = SimpleUploadedFile("icon_to_update.svg", b"<svg>Old content</svg>", content_type="image/svg+xml")
    TrafficControlDeviceTypeIcon.objects.create(file=svg_file)
    assert TrafficControlDeviceTypeIcon.objects.count() == 1
    updated_icon = TrafficControlDeviceTypeIcon.objects.get(file__endswith="icon_to_update.svg")

    # Sanity check, the existing icon has the old content
    with updated_icon.file.open("rb") as f:
        old_content = f.read()
    assert old_content == b"<svg>Old content</svg>"

    call_command("upload_static_svg_icons_to_blobstorage")
    captured = capsys.readouterr()

    # Verify final state of the database
    assert TrafficControlDeviceTypeIcon.objects.count() == 3

    # Check for expected output messages
    assert "Icon created" in captured.out
    assert "Icon updated" in captured.out
    assert "Icon upload to blobstorage complete." in captured.out

    # Check that the uploaded file was updated
    updated_icon = TrafficControlDeviceTypeIcon.objects.get(file__endswith="icon_to_update.svg")
    with updated_icon.file.open("rb") as f:
        new_content = f.read()

    assert new_content == b"<svg>New content</svg>\n"
    assert new_content != old_content
