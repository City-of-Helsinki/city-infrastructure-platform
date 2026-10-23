import pytest
from django.core.management import call_command, CommandError

from city_furniture.models import FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceType
from city_furniture.tests.factories import get_city_furniture_color
from traffic_control.models import MountType


@pytest.mark.django_db
def test_raise_command_error_if_no_file_found():
    with pytest.raises(CommandError):
        call_command("import_furniture_signpost_reals_kantakaupunki", "dummy.csv")


@pytest.mark.django_db
def test_import_furniture_signposts_success(datadir):
    # Setup device types
    for code in [
        "Rantareitti-1A",
        "Rantareitti-1B",
        "Rantareitti-2A",
        "Rantareitti-2B",
        "Rantareitti-3",
        "Rantareitti-4A",
        "Rantareitti-4B",
        "Rantareitti-5",
    ]:
        CityFurnitureDeviceType.objects.create(
            code=code,
            class_type="1030",
            function_type="1090",
            target_model="furniture_signpost",
        )
    MountType.objects.get_or_create(code="LIGHTPOLE", description="pole", description_fi="Katuvalopylväs")
    MountType.objects.get_or_create(code="POLE", description="pole", description_fi="Opaste")

    get_city_furniture_color("Kantakaupunki")

    call_command("import_furniture_signpost_reals_kantakaupunki", datadir / "success.csv")

    assert FurnitureSignpostReal.objects.count() == 7
    fsr = FurnitureSignpostReal.objects.first()
    assert fsr.source_name == "Kantakaupungin Rantareitti 2022 csv"
