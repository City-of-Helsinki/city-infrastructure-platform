from collections import UserDict
from unittest.mock import patch

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.core.management import call_command
from django.test import TestCase

from traffic_control.models.affect_area import ParkingArea, ParkingAreaCategory
from traffic_control.tests.test_base_api import test_multi_polygon


class MockAttribute:
    def __init__(self, value):
        self.value = value


class MockFeature(UserDict):
    def __init__(self, data, ogr_geom):
        super().__init__(data)
        self.geom = ogr_geom


MOCK_FEATURE_1 = MockFeature(
    {
        "id": MockAttribute(1),
        "luokka": MockAttribute(100),
        "luokka_nimi": MockAttribute("category 1"),
        "tyyppi": MockAttribute("type 1"),
        "kausi": MockAttribute("summer"),
        "asukaspysakointitunnus": MockAttribute("P"),
        "paikan_asento": MockAttribute("facing street"),
        "voimassaolo": MockAttribute("valid"),
        "kesto": MockAttribute("4h"),
        "pinta_ala": MockAttribute(120),
        "paikat_ala": MockAttribute(20),
        "lisatieto": MockAttribute("test description"),
        "pysayttamiskielto": MockAttribute("stopping not allowed"),
        "paivitetty_tietopalveluun": MockAttribute("2020-10-01"),
        "datanomistaja": MockAttribute("dummy"),
    },
    test_multi_polygon.ogr,
)

MOCK_FEATURE_2 = MockFeature(
    {
        "id": MockAttribute(2),
        "luokka": MockAttribute(100),
        "luokka_nimi": MockAttribute("category 1"),
        "tyyppi": MockAttribute("type 1"),
        "kausi": MockAttribute("summer"),
        "asukaspysakointitunnus": MockAttribute("P"),
        "paikan_asento": MockAttribute("facing street"),
        "voimassaolo": MockAttribute("valid"),
        "kesto": MockAttribute("4h"),
        "pinta_ala": MockAttribute(120),
        "paikat_ala": MockAttribute(20),
        "lisatieto": MockAttribute("test description"),
        "pysayttamiskielto": MockAttribute("stopping not allowed"),
        "paivitetty_tietopalveluun": MockAttribute("2020-10-01"),
        "datanomistaja": MockAttribute("dummy"),
    },
    test_multi_polygon.ogr,
)


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


class ImportParkingAreaTestCase(TestCase):
    @patch("urllib.request.urlretrieve", return_value=("dummy-file", {}))
    @patch(
        "traffic_control.management.commands.import_parking_areas_hki_wfs.DataSource",
        MockDataSource,
    )
    def test_importer_created_operational_areas(self, mock_urlretrieve):
        call_command("import_parking_areas_hki_wfs")
        self.assertEqual(ParkingArea.objects.count(), 2)
        self.assertEqual(ParkingAreaCategory.objects.count(), 1)
