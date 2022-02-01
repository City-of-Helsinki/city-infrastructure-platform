import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from city_furniture.models.common import CityFurnitureDeviceType
from traffic_control.tests.management.commands.utils import mock_open


class ImportTrafficControlDeviceTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(CommandError, call_command, "import_city_furniture_device_types", "dummy.csv")

    @patch("os.path.exists", return_value=True)
    def test_import_city_furniture_device_types_success(self, mock_exists):
        data = os.linesep.join(
            [
                "code,class_type,function_type,icon,description,size,target_model",
                "C3-A,1030,1090,,Opasteet matala,300 * 400,furniture_signpost",
                "C3-B,1030,1090,,Opasteet matala,600 * 400,furniture_signpost",
                "C3-B,1030,1090,,Opasteet matala,900 * 400,furniture_signpost",
                "C3-B,1030,1090,,Opasteet matala,1200 * 400,furniture_signpost",
            ]
        )

        with patch(
            "city_furniture.management.commands.import_city_furniture_device_types.open",
            mock_open(read_data=data),
        ):
            call_command("import_city_furniture_device_types", "test-data.csv")
            self.assertEqual(CityFurnitureDeviceType.objects.count(), 2)
            self.assertEqual(CityFurnitureDeviceType.objects.get(code="C3-A").size, "300 * 400")
            self.assertEqual(CityFurnitureDeviceType.objects.get(code="C3-B").size, "1200 * 400")
