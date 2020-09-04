from collections import UserDict
from unittest.mock import patch

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.core.management import call_command
from django.test import TestCase

from traffic_control.models import OperationalArea
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
        "nimi": MockAttribute("feature 1"),
        "nimi_lyhyt": MockAttribute("f1"),
        "urakkamuoto": MockAttribute("area type 1"),
        "urakoitsija": MockAttribute("contractor 1"),
        "alku_pvm": MockAttribute("2020-01-01"),
        "loppu_pvm": MockAttribute("2020-12-31"),
        "paivitetty_tietopalveluun": MockAttribute("2020-08-01"),
        "tehtavakokonaisuus": MockAttribute("KATU"),
        "status": MockAttribute("ready"),
    },
    test_multi_polygon.ogr,
)

MOCK_FEATURE_2 = MockFeature(
    {
        "id": MockAttribute(2),
        "nimi": MockAttribute("feature 2"),
        "nimi_lyhyt": MockAttribute("f2"),
        "urakkamuoto": MockAttribute("area type 2"),
        "urakoitsija": MockAttribute("contractor 2"),
        "alku_pvm": MockAttribute("2020-01-01"),
        "loppu_pvm": MockAttribute("2020-12-31"),
        "paivitetty_tietopalveluun": MockAttribute("2020-08-01"),
        "tehtavakokonaisuus": MockAttribute("OTHER-TASK"),
        "status": MockAttribute("ready"),
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


class ImportOperationalAreasHkiWfsTestCase(TestCase):
    @patch("urllib.request.urlretrieve", return_value=("dummy-file", {}))
    @patch(
        "traffic_control.management.commands.import_operational_areas_hki_wfs.DataSource",
        MockDataSource,
    )
    def test_importer_created_operational_areas(self, mock_urlretrieve):
        call_command("import_operational_areas_hki_wfs")
        self.assertEqual(OperationalArea.objects.count(), 1)
        imported_feature = OperationalArea.objects.first()
        self.assertEqual(imported_feature.source_id, "1")
