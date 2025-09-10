import os
from tempfile import TemporaryDirectory

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from city_furniture.models.common import CityFurnitureDeviceTypeIcon

EXAMPLE_SVG_NAME = "test_city_furniture_device_type_icon__svg.svg"
EXAMPLE_PNG_NAME = "test_city_furniture_device_type_icon__svg.png"
INCOMING_SVG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXAMPLE_SVG_NAME)


@pytest.fixture
def override_settings(settings):
    settings.MEDIA_ROOT = TemporaryDirectory().name


@pytest.fixture
def svg_file():
    with open(INCOMING_SVG_PATH, "rt") as fin:
        svg_bytestring = fin.read()
        return SimpleUploadedFile(EXAMPLE_SVG_NAME, bytes(svg_bytestring, "utf-8"), content_type="image/svg+xml")


@pytest.mark.xfail(reason="Requires azurite storage or django >=5.1+, django 4.2 simply renames the file")
@pytest.mark.django_db
def test__city_furniture_device_type_icon__enforces_uniqueness(override_settings, svg_file):
    """
    We don't want two separate rows meaning city_furniture_traffic_stop_1.svg in our table, as it would produce an
    unintended 'overwrite generated PNGs' effect on creation of a duplicate or 'delete PNGs that should be preserved'
    effect in the deletion of a duplicate due to the custom signal handlers related to this model.
    """
    CityFurnitureDeviceTypeIcon.objects.create(file=svg_file)
    with pytest.raises(IntegrityError):
        CityFurnitureDeviceTypeIcon.objects.create(file=svg_file)


@pytest.mark.django_db
def test__city_furniture_device_type_icon__custom_signal_handlers(override_settings, svg_file, settings):
    """
    Creating CityFurnitureDeviceTypeIcon objects triggers as a side effect the creation of PNG icons in different sizes
    corresponding to the uploaded SVG. Check the following:
    * The SVG and its corresponding PNG files are found in expected places after creation.
    * The SVG and its corresponding PNG files are wiped from disk after deletion.
    """
    td = CityFurnitureDeviceTypeIcon.objects.create(file=svg_file)
    storage = td.file.storage

    # NOTE (2025-09-17 thiago)
    # This test is written with big faith in WORKS ON MY MACHINE - At least locally, running this test doesn't seem to
    # require any sort of waiting before checking that the custom signal handlers for post_save and post_delete have
    # taken effect. In case this test is flakey consider introducing some sort of waiting here.

    # Check that after object creation the files are in the right place
    assert storage.exists(os.path.join(settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION, EXAMPLE_SVG_NAME))
    for size in settings.PNG_ICON_SIZES:
        assert storage.exists(
            os.path.join(
                settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION,
                str(size),
                EXAMPLE_PNG_NAME,
            )
        )

    # Check that after object deletion the files have been wiped
    td.delete()
    assert not storage.exists(os.path.join(settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION, EXAMPLE_SVG_NAME))
    for size in settings.PNG_ICON_SIZES:
        assert not storage.exists(
            os.path.join(
                settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION,
                str(size),
                EXAMPLE_PNG_NAME,
            )
        )
