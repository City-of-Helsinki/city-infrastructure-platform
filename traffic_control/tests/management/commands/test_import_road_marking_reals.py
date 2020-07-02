import os
from unittest.mock import mock_open, patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import RoadMarkingReal, TrafficControlDeviceType


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

        # mock_open does not implement required dunder methods
        # in order to be consumable by csv.reader. There's an
        # open issue regarding this: https://bugs.python.org/issue21258
        m = mock_open(read_data=data)
        m.return_value.__iter__ = lambda f: f
        m.return_value.__next__ = lambda f: next(iter(f.readline, ""))

        with patch(
            "traffic_control.management.commands.import_road_marking_reals.open", m
        ):
            call_command("import_road_marking_reals", "test-data.csv")
            self.assertEqual(RoadMarkingReal.objects.count(), 3)
