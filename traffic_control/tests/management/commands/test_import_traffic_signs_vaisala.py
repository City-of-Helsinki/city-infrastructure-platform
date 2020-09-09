import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import AdditionalSignReal, TrafficSignReal

from .utils import mock_open


class ImportTrafficControlDeviceTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError,
            call_command,
            "import_traffic_signs_vaisala",
            "dummy.csv",
        )

    @patch("os.path.exists", return_value=True)
    def test_import_traffic_signs_success(self, mock_exists):
        data = os.linesep.join(
            [
                "id,longitude,latitude,elevation,label,name,code,additional_info,condition,action,category,heading,number_of_videos,accuracy,detection_confidence,localization_confidence,text,last_detected,frame_url,map_url,direction,side,address_id,address_km,address_m",  # noqa: E501
                "id-1,24.1887647745,60.1006972294,10,,,A1,,,,,,,,,,,2020-06-15T06:32:11.453Z,https://example.com/1,,,left,,,",  # noqa: E501
                "id-2,24.3746164964,60.3863144666,10,,,B2,,,,,,,,,,,2020-06-15T06:27:09.998Z,https://example.com/2,,,right,,,",  # noqa: E501
                "id-3,24.3523944777,60.4773050631,10,,,C3,,,,,,,,,,,2020-06-30T03:27:09.998Z,https://example.com/3,,,right,,,",  # noqa: E501
                "id-3,24.3523944777,60.4773050631,10,,,C3,,,,,,,,,,,2020-06-30T03:27:09.998Z,https://example.com/3,,,right,,,",  # noqa: E501
                "id-4,24.3523944777,60.4773050631,10,,,80,,,,,,,,,,,2020-06-30T03:27:09.998Z,https://example.com/3,,,right,,,",  # noqa: E501
                "id-5,24.3523944777,60.4773050631,10,,,88,,,,,,,,,,,2020-06-30T03:27:09.998Z,https://example.com/3,,,right,,,",  # noqa: E501
            ]
        )

        with patch(
            "traffic_control.management.commands.import_traffic_signs_vaisala.open",
            mock_open(read_data=data),
        ):
            call_command("import_traffic_signs_vaisala", "test-data.csv")
            self.assertEqual(TrafficSignReal.objects.count(), 3)
            self.assertEqual(AdditionalSignReal.objects.count(), 2)
