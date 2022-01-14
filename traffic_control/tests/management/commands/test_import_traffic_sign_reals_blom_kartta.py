import datetime
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.core.management import call_command, CommandError
from django.test import TestCase
from pytz import timezone

from traffic_control.enums import DeviceTypeTargetModel
from traffic_control.models import (
    AdditionalSignContentReal,
    AdditionalSignReal,
    MountType,
    TrafficControlDeviceType,
    TrafficSignReal,
)

MOCK_FEATURE_1 = {
    "fid": "1",
    "mount_type": "Wall",
    "date": "2020-08-04 12:00:00",
    "type": "101",
    "text": "4,05t",
    "x": 2776957,
    "y": 8442622,
    "z": 0.5,
}
MOCK_FEATURE_2 = {
    "fid": "2",
    "mount_type": "Poll",
    "date": "2020-08-01 12:00:00",
    "type": "808",
    "text": "additional sign info",
    "x": 2776958,
    "y": 8442623,
    "z": 0.8,
}


class MockLayer:
    def __init__(self):
        self.srs = SpatialReference(settings.SRID)
        self.mock_features = [
            MOCK_FEATURE_1,
            MOCK_FEATURE_2,
        ]

    def __iter__(self):
        yield from self.mock_features

    def __len__(self):
        return len(self.mock_features)


class MockDataSource:
    def __init__(self, ds_input):
        pass

    def __getitem__(self, index):
        return MockLayer()


class ImportTrafficSignRealsBlomKarttaTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError,
            call_command,
            "import_traffic_sign_reals_blom_kartta",
            "-f",
            "dummy.shp",
        )

    @patch("os.path.exists", return_value=True)
    @patch(
        "traffic_control.management.commands.import_traffic_sign_reals_blom_kartta.DataSource",
        MockDataSource,
    )
    def test_import_traffic_sign_reals_blom_kartta_success(self, mock_exists):
        device_type = TrafficControlDeviceType.objects.create(
            code="ABC",
            legacy_code="808",
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
        )

        call_command("import_traffic_sign_reals_blom_kartta", "-f", "dummy.csv")
        # verify main traffic sign is imported
        self.assertEqual(TrafficSignReal.objects.count(), 1)
        # verify additional sign is imported
        self.assertEqual(AdditionalSignReal.objects.count(), 1)
        # verify mount type objects are created
        self.assertEqual(MountType.objects.count(), 2)

        traffic_sign = TrafficSignReal.objects.first()
        # verify imported time has tz info
        expected_time = datetime.datetime(2020, 8, 4, 9, 0, 0, tzinfo=timezone("UTC"))
        self.assertEqual(traffic_sign.scanned_at, expected_time)
        # verify text is imported for main traffic sign
        self.assertEqual(traffic_sign.txt, "4,05t")
        # verify numeric value is extracted from text and assign to value field
        self.assertEqual(traffic_sign.value, Decimal("4.05"))
        additional_sign = AdditionalSignReal.objects.first()
        # verify additional content is created
        additional_sign_content = AdditionalSignContentReal.objects.first()
        self.assertEqual(additional_sign_content.parent, additional_sign)
        self.assertEqual(additional_sign_content.text, "additional sign info")
        # verify additional sign content is assigned correct device_type
        self.assertEqual(additional_sign_content.device_type, device_type)
