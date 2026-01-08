import os
from tempfile import TemporaryDirectory

import pytest
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from traffic_control.models.common import TrafficControlDeviceTypeIcon


@pytest.fixture
def mock_static_dir():
    """
    Creates a temporary directory to mock the static files location.
    """
    with TemporaryDirectory() as tmp_dir:
        # Construct the path that the Django command expects
        static_dir = os.path.join(tmp_dir, "static", "traffic_control", "svg", "traffic_sign_icons")
        os.makedirs(static_dir)

        # Create some dummy SVG files for the test
        with open(os.path.join(static_dir, "icon1.svg"), "w") as f:
            f.write("<svg>content1</svg>")
        with open(os.path.join(static_dir, "icon2.svg"), "w") as f:
            f.write("<svg>content2</svg>")
        with open(os.path.join(static_dir, "icon_to_update.svg"), "w") as f:
            f.write("<svg>New content</svg>")

        # Temporarily change the app's path to our temporary directory
        original_app_path = apps.get_app_config("traffic_control").path
        apps.get_app_config("traffic_control").path = tmp_dir

        yield static_dir

        # Restore the original app path after the test
        apps.get_app_config("traffic_control").path = original_app_path


@pytest.mark.django_db
def test__upload_static_svg_icons_to_blobstorage__command_creates_icons(mock_static_dir, capsys):
    """
    Verifies that the command correctly creates new TrafficControlDeviceTypeIcon objects for each new file
    """
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
def test__upload_static_svg_icons_to_blobstorage__command_creates_and_updates_icons(mock_static_dir, capsys):
    """
    Verifies that the command correctly creates new TrafficControlDeviceTypeIcon objects for each new file and updates
    existing TrafficControlDeviceTypeIcon objects.
    """
    assert TrafficControlDeviceTypeIcon.objects.count() == 0

    # Create an existing icon that the command should update
    old_content = b"<svg>Old content</svg>"
    svg_file = SimpleUploadedFile("icon_to_update.svg", old_content, content_type="image/svg+xml")
    TrafficControlDeviceTypeIcon.objects.create(file=svg_file)
    assert TrafficControlDeviceTypeIcon.objects.count() == 1

    call_command("upload_static_svg_icons_to_blobstorage")
    captured = capsys.readouterr()

    # Verify final state of the database
    assert TrafficControlDeviceTypeIcon.objects.count() == 3  # The test will break here when django < 5.1

    # Check for expected output messages
    assert "Icon created" in captured.out
    assert "Icon updated" in captured.out
    assert "Icon upload to blobstorage complete." in captured.out

    # Check that the uploaded file was updated
    updated_icon = TrafficControlDeviceTypeIcon.objects.get(file__endswith="icon_to_update.svg")
    with updated_icon.file.open("rb") as f:
        new_content = f.read()

    assert new_content == b"<svg>New content</svg>"
    assert new_content != old_content
