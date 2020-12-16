import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from traffic_control.models import (
    AdditionalSignContentReal,
    AdditionalSignReal,
    TrafficControlDeviceType,
    TrafficSignReal,
)
from traffic_control.models.common import DeviceTypeTargetModel

from .utils import mock_open


class ImportTrafficControlDeviceTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError,
            call_command,
            "import_traffic_sign_reals_vaisala",
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
            "traffic_control.management.commands.import_traffic_sign_reals_vaisala.open",
            mock_open(read_data=data),
        ):
            for legacy_code in ["A1", "B2", "C3"]:
                TrafficControlDeviceType.objects.create(
                    code=f"CODE-{legacy_code}",
                    legacy_code=legacy_code,
                    target_model=DeviceTypeTargetModel.TRAFFIC_SIGN,
                )
            for legacy_code in ["80", "88"]:
                TrafficControlDeviceType.objects.create(
                    code=f"CODE-{legacy_code}",
                    legacy_code=legacy_code,
                    target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
                )
            call_command("import_traffic_sign_reals_vaisala", "test-data.csv")
            self.assertEqual(TrafficSignReal.objects.count(), 3)
            traffic_sign_device_types = dict(
                TrafficSignReal.objects.values_list("source_id", "device_type__code")
            )
            expected_traffic_sign_device_types = {
                "id-1": "CODE-A1",
                "id-2": "CODE-B2",
                "id-3": "CODE-C3",
            }
            self.assertDictEqual(
                traffic_sign_device_types, expected_traffic_sign_device_types
            )
            self.assertEqual(AdditionalSignReal.objects.count(), 2)
            additional_sign_device_types = dict(
                AdditionalSignContentReal.objects.values_list(
                    "parent__source_id", "device_type__code"
                )
            )
            expected_additional_sign_device_types = {
                "id-4": "CODE-80",
                "id-5": "CODE-88",
            }
            self.assertDictEqual(
                additional_sign_device_types, expected_additional_sign_device_types
            )
