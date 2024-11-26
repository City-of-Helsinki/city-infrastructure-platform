import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import RoadMarkingReal, TrafficControlDeviceType
from traffic_control.tests.management.commands.utils import mock_open
from traffic_control.tests.utils import MIN_X, MIN_Y


class ImportPortalTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(CommandError, call_command, "import_road_marking_reals", "dummy.csv")

    @patch("os.path.exists", return_value=True)
    def test_import_road_marking_success(self, mock_exists):
        TrafficControlDeviceType.objects.create(code="M1")
        data = os.linesep.join(
            [
                "id;xcoord;ycoord;Tyyppi koo;Nuolen suu;Pituus;Väri;m_arvo;Lisätieto",
                f"1;{MIN_X+2000};{MIN_Y+6000};M1;F;;;;info",
                f"2;{MIN_X+2100};{MIN_Y+6100};M1;F;;;;info",
                f"2;{MIN_X+2100};{MIN_Y+6100};M1;F;;;;info",
                f"3;{MIN_X+2200};{MIN_Y+6200};M1;F;;;;info",
                f"3;{MIN_X+2300};{MIN_Y+6300};M1;F;;;;info",
            ]
        )

        with patch(
            "traffic_control.management.commands.import_road_marking_reals.open",
            mock_open(read_data=data),
        ):
            call_command("import_road_marking_reals", "test-data.csv")
            self.assertEqual(RoadMarkingReal.objects.count(), 3)
