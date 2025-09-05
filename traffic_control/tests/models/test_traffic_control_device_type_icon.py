import os
from tempfile import TemporaryDirectory

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError

from traffic_control.models.common import TrafficControlDeviceTypeIcon

EXAMPLE_SVG_NAME = "test_traffic_control_device_type_icon__A.svg"
EXAMPLE_PNG_NAME = "test_traffic_control_device_type_icon__A.png"
INCOMING_SVG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXAMPLE_SVG_NAME)


@pytest.fixture
def override_settings(settings):
    settings.MEDIA_ROOT = TemporaryDirectory().name


@pytest.fixture
def svg_file():
    with open(INCOMING_SVG_PATH, "rt") as fin:
        svg_bytestring = fin.read()
        return SimpleUploadedFile(EXAMPLE_SVG_NAME, bytes(svg_bytestring, "utf-8"), content_type="image/svg+xml")


@pytest.mark.xfail(reason="Requires azurite storage or django >=5.1+, django 4.2 simply renames file")
@pytest.mark.django_db
def test__traffic_control_device_type_icon__enforces_uniqueness(override_settings, svg_file):
    """
    We don't want two separate rows meaning traffic_control_traffic_stop_1.svg in our table, as it would produce an
    unintended 'overwrite generated PNGs' effect on creation of a duplicate or 'delete PNGs that should be preserved'
    effect in the deletion of a duplicate due to the custom signal handlers related to this model.
    """
    TrafficControlDeviceTypeIcon.objects.create(file=svg_file)
    with pytest.raises(IntegrityError):
        TrafficControlDeviceTypeIcon.objects.create(file=svg_file)
