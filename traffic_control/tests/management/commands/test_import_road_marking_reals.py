import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import RoadMarkingReal, TrafficControlDeviceType

from .utils import mock_open


class ImportPortalTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError, call_command, "import_road_marking_reals", "dummy.csv"
        )

    @patch("os.path.exists", return_value=True)
    def test_import_portal_types_success(self, mock_exists):
        TrafficControlDeviceType.objects.create(code="M1")
        data = os.linesep.join(
            [
                "id;xcoord;ycoord;Tyyppi koo;Nuolen suu;Pituus;Väri;m_arvo;Lisätieto",
                "1;2000000;6000000;M1;F;;;;info",
                "2;2100000;6100000;M1;F;;;;info",
                "2;2100000;6100000;M1;F;;;;info",
                "3;2200000;6200000;M1;F;;;;info",
                "3;2300000;6300000;M1;F;;;;info",
            ]
        )

        with patch(
            "traffic_control.management.commands.import_road_marking_reals.open",
            mock_open(read_data=data),
        ):
            call_command("import_road_marking_reals", "test-data.csv")
            self.assertEqual(RoadMarkingReal.objects.count(), 3)
