import os
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from city_furniture.models import FurnitureSignpostReal
from city_furniture.models.common import CityFurnitureDeviceType
from city_furniture.tests.factories import get_city_furniture_color
from traffic_control.models import MountType
from traffic_control.tests.management.commands.utils import mock_open


class ImportTrafficControlDeviceTypesTestCase(TestCase):
    def test_raise_command_error_if_no_file_found(self):
        self.assertRaises(
            CommandError,
            call_command,
            "import_furniture_signpost_reals_kantakaupunki",
            "dummy.csv",
        )

    @patch("os.path.exists", return_value=True)
    def test_import_furniture_signposts_success(self, mock_exists):
        data = os.linesep.join(
            [
                "id,device_type,latitude,longitude,location_name_fi,direction,height,order,mount_type,arrow_direction,sign_color,pictogram,value,text_content_fi,text_content_sw,text_content_en,content_responsible_entity,validity_period_start,validity_period_end,additional_material_url",  # noqa: E501
                "A42,reittivahvennelaatta,25497601.12758740,6672058.993934970,Laivasillankatu,45,140,,Tolppa,,Kantakaupunki,,,,,,,,,,",  # noqa: E501
                "A1B,reittivahvennelaatta,25497601.12758740,6672058.993934970,JokuKatu,0,220,1,Katuvalopylväs,UP,Kantakaupunki,piktogrammi,,Suomi,Svenska,English,Kaupunki,2020-01-01,2020-12-31,https://example.com/",  # noqa: E501
                "A2B,tarrat,25496195.72344000,6673869.586320790,JokuKatu,0,220,1,Katuvalopylväs,UP,Kantakaupunki,piktogrammi,,Suomi,Svenska,English,Kaupunki,2020-01-01,2020-12-31,https://example.com/",  # noqa: E501
                "A3B,kartat,25497707.19834310,6672915.894190060,JokuKatu,0,220,1,Tolppa,UP,Kantakaupunki,piktogrammi,,Suomi,Svenska,English,Kaupunki,2020-01-01,2020-12-31,https://example.com/",  # noqa: E501
                "A4B,pollarit,25496702.18210040,6671287.668982360,JokuKatu,0,220,1,Tolppa,BOTTOM_RIGHT,Kantakaupunki,piktogrammi,,Suomi,Svenska,English,Kaupunki,2020-01-01,2020-12-31,https://example.com/",  # noqa: E501
                "A5B,viitat,25495251.56117200,6672573.32108099,JokuKatu,0,220,1,Tolppa,DOWN,Kantakaupunki,piktogrammi,500,Suomi,Svenska,English,Kaupunki,2020-01-01,2020-12-31,https://example.com/",  # noqa: E501
                "A6B,viitat,25495251.56117200,6672573.32108099,,,,,,,,,,,,,,,,",
            ]
        )

        with patch(
            "city_furniture.management.commands.import_furniture_signpost_reals_kantakaupunki.open",
            mock_open(read_data=data),
        ):
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

            call_command("import_furniture_signpost_reals_kantakaupunki", "test-data.csv")

            self.assertEqual(FurnitureSignpostReal.objects.count(), 7)
            fsr = FurnitureSignpostReal.objects.first()
            self.assertEqual(fsr.source_name, "Kantakaupungin Rantareitti 2022 csv")
