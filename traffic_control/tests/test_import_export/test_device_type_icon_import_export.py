from pathlib import Path

import pytest
from tablib import Dataset

from traffic_control.models import TrafficControlDeviceTypeIcon
from traffic_control.resources.device_type_icon import TrafficControlDeviceTypeIconResource
from traffic_control.tests.factories import TrafficControlDeviceTypeIconFactory
from traffic_control.tests.test_import_export.utils import file_formats


@pytest.mark.django_db
def test__traffic_control_device_type_icon__export():
    """Test simple export of a single traffic control device type icon"""
    icon = TrafficControlDeviceTypeIconFactory(file__filename="test.svg")
    dataset = TrafficControlDeviceTypeIconResource().export()

    assert len(dataset) == 1
    assert dataset.dict[0]["file"] == icon.file.name
    assert "id" not in dataset.dict[0]


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type_icon__import_create(temp_icon_storage, format):
    """Test simple import of a single traffic control device type icon"""
    # Create a dummy file to be imported
    # The file needs to exist in the media folder for the import to work
    # as the post-save signal tries to read it to generate pngs.
    svg_file_path = Path(temp_icon_storage) / "test.svg"
    svg_file_path.parent.mkdir(parents=True, exist_ok=True)
    svg_file_path.touch()

    data = {
        "file": "test.svg",
    }
    dataset = Dataset()
    dataset.headers = data.keys()
    dataset.append(data.values())

    assert TrafficControlDeviceTypeIcon.objects.count() == 0

    result = TrafficControlDeviceTypeIconResource().import_data(dataset, raise_errors=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert result.totals["new"] == 1
    assert result.totals["update"] == 0
    assert TrafficControlDeviceTypeIcon.objects.count() == 1
    imported_icon = TrafficControlDeviceTypeIcon.objects.first()
    assert imported_icon.file.name == data["file"]


@pytest.mark.parametrize("format", file_formats)
@pytest.mark.django_db
def test__traffic_control_device_type_icon__import_skip(temp_icon_storage, format):
    """Test that importing an existing icon is skipped"""
    icon = TrafficControlDeviceTypeIconFactory(file__filename="test.svg")

    # The file needs to exist in the media folder for the import to work.
    # The factory will create the file in the right location inside the
    # temp_icon_storage.
    assert (Path(temp_icon_storage) / icon.file.name).exists()

    data = {
        "file": icon.file.name,
    }
    dataset = Dataset()
    dataset.headers = data.keys()
    dataset.append(data.values())

    assert TrafficControlDeviceTypeIcon.objects.count() == 1

    result = TrafficControlDeviceTypeIconResource().import_data(dataset, raise_errors=True)

    assert not result.has_validation_errors()
    assert not result.has_errors()
    assert result.totals["new"] == 0
    assert result.totals["update"] == 0
    assert result.totals["skip"] == 1
    assert TrafficControlDeviceTypeIcon.objects.count() == 1
    imported_icon = TrafficControlDeviceTypeIcon.objects.first()
    assert imported_icon.id == icon.id
    assert imported_icon.file.name == data["file"]
