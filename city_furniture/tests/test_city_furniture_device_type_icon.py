import os

import pytest
from django.core.files.base import ContentFile
from django.db import IntegrityError

from city_furniture.models.common import CityFurnitureDeviceTypeIcon

EXAMPLE_SVG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_city_furniture_device_type_icon__svg.svg"
)


@pytest.mark.xfail(reason="Requires azurite storage or django >=5.1+, django 4.2 simply renames the file")
@pytest.mark.django_db
def test__city_furniture_device_type_icon__enforces_uniqueness():
    """
    We don't want two separate rows meaning city_furniture_traffic_stop_1.svg in our table, as it would produce an
    unintended 'overwrite generated PNGs' effect on creation of a duplicate or 'delete PNGs that should be preserved'
    effect in the deletion of a duplicate due to the custom signal handlers related to this model.
    """
    with open(EXAMPLE_SVG_PATH, "rt") as fin:
        svg_bytestring = fin.read()
        svg_file_content = ContentFile(svg_bytestring)
    CityFurnitureDeviceTypeIcon.objects.create(file=svg_file_content)
    with pytest.raises(IntegrityError):
        CityFurnitureDeviceTypeIcon.objects.create(file=svg_file_content)
