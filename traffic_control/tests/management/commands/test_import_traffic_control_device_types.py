import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models.common import TrafficControlDeviceType

from .utils import mock_open


class ImportTrafficControlDeviceTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError,
            call_command,
            "import_traffic_control_device_types",
            "dummy.csv",
        )

    @patch("os.path.exists", return_value=True)
    def test_import_portal_types_success(self, mock_exists):
        data = os.linesep.join(
            [
                "MerkkiKoodi,Kuvaus,NykyinenLiisussaTunnus,NykyinenLiisussaNimi,Tyypi",
                "1,Kiinteä punainen valo ,,,",
                "K1,Keskiviiva ,,,longitudinal",
                "K1,Keskiviiva ,,,longitudinal",
                "K1,Keskiviiva ,,,longitudinal",
            ]
        )

        with patch(
            "traffic_control.management.commands.import_traffic_control_device_types.open",
            mock_open(read_data=data),
        ):
            call_command("import_traffic_control_device_types", "test-data.csv")
            self.assertEqual(TrafficControlDeviceType.objects.count(), 2)
