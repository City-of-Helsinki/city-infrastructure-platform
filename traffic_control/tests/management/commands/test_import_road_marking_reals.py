import pytest
from django.core.management import call_command, CommandError

from traffic_control.models import RoadMarkingReal, TrafficControlDeviceType
from traffic_control.tests.utils import MIN_X, MIN_Y


@pytest.mark.django_db
def test_raise_command_error_if_no_file_found():
    with pytest.raises(CommandError):
        call_command("import_road_marking_reals", "missing.csv")


@pytest.mark.django_db
def test_import_road_marking_success(tmp_path):
    TrafficControlDeviceType.objects.create(code="M1")
    # NOTE (thiago 2026-10-29) We need to write the file like this because we depend on constants from python files
    with open(tmp_path / "success.csv", "wt") as f_in:
        f_in.write(
            "id;xcoord;ycoord;Tyyppi koo;Nuolen suu;Pituus;Väri;m_arvo;Lisätieto\n"
            f"1;{MIN_X + 2000};{MIN_Y + 6000};M1;F;;;;info\n"
            f"2;{MIN_X + 2100};{MIN_Y + 6100};M1;F;;;;info\n"
            f"2;{MIN_X + 2100};{MIN_Y + 6100};M1;F;;;;info\n"
            f"3;{MIN_X + 2200};{MIN_Y + 6200};M1;F;;;;info\n"
            f"3;{MIN_X + 2300};{MIN_Y + 6300};M1;F;;;;info\n"
        )

    call_command("import_road_marking_reals", tmp_path / "success.csv")
    assert RoadMarkingReal.objects.count() == 3
