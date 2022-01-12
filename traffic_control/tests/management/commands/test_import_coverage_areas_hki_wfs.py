from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from traffic_control.models.affect_area import CoverageArea, CoverageAreaCategory
from traffic_control.tests.management.commands.utils import create_mock_data_source, MockAttribute, MockFeature
from traffic_control.tests.test_base_api import test_multi_polygon

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


class ImportCoverageAreaTestCase(TestCase):
    @patch("urllib.request.urlretrieve", return_value=("dummy-file", {}))
    @patch(
        "traffic_control.management.commands.import_coverage_areas_hki_wfs.DataSource",
        create_mock_data_source([MOCK_FEATURE_1, MOCK_FEATURE_2]),
    )
    def test_importer_created_coverage_areas(self, mock_urlretrieve):
        call_command("import_coverage_areas_hki_wfs")
        self.assertEqual(CoverageArea.objects.count(), 2)
        self.assertEqual(CoverageAreaCategory.objects.count(), 1)
