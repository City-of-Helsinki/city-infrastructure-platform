from datetime import date
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from traffic_control.models import OperationalArea
from traffic_control.tests.factories import OperationalAreaFactory
from traffic_control.tests.management.commands.utils import create_mock_data_source, MockAttribute, MockFeature
from traffic_control.tests.test_base_api import test_multi_polygon

MOCK_FEATURE_0 = MockFeature(
    {
        "id": MockAttribute(0),
        "nimi": MockAttribute("feature 0 (updated)"),
        "nimi_lyhyt": MockAttribute("f0"),
        "urakkamuoto": MockAttribute("area type 0"),
        "urakoitsija": MockAttribute("contractor 0"),
        "alku_pvm": MockAttribute("2019-01-01"),
        "loppu_pvm": MockAttribute("2019-12-31"),
        "paivitetty_tietopalveluun": MockAttribute("2019-08-01"),
        "tehtavakokonaisuus": MockAttribute("KATU"),
        "status": MockAttribute("ready"),
    },
    test_multi_polygon.ogr,
)


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
        "alku_pvm": MockAttribute("2020-02-01"),
        "loppu_pvm": MockAttribute("2020-11-31"),
        "paivitetty_tietopalveluun": MockAttribute("2020-07-01"),
        "tehtavakokonaisuus": MockAttribute("OTHER-TASK"),
        "status": MockAttribute("not ready"),
    },
    test_multi_polygon.ogr,
)


@pytest.mark.django_db
def test_importer_created_operational_areas():
    oa_0 = OperationalAreaFactory(name="feature 0", source_id=0, source_name="urakkarajat_katu")
    patch_url = patch(
        "traffic_control.management.commands.import_operational_areas_hki_wfs.urlretrieve",
        return_value=("dummy-file", {}),
    )
    patch_ds = patch(
        "traffic_control.management.commands.import_operational_areas_hki_wfs.DataSource",
        new=create_mock_data_source([MOCK_FEATURE_0, MOCK_FEATURE_1, MOCK_FEATURE_2]),
    )
    out = StringIO()

    with patch_url, patch_ds:
        call_command("import_operational_areas_hki_wfs", stdout=out)

    assert OperationalArea.objects.count() == 2, "The command only imports OperationalAreas that fit its criteria"

    imported_feature = OperationalArea.objects.get(name="feature 1")
    assert imported_feature.source_id == "1"
    assert imported_feature.name == "feature 1"
    assert imported_feature.name_short == "f1"
    assert imported_feature.area_type == "area type 1"
    assert imported_feature.contractor == "contractor 1"
    assert imported_feature.start_date == date(2020, 1, 1)
    assert imported_feature.end_date == date(2020, 12, 31)
    assert imported_feature.updated_date == date(2020, 8, 1)
    assert imported_feature.task == "KATU"
    assert imported_feature.status == "ready"
    oa_0.refresh_from_db()
    assert oa_0.name == "feature 0 (updated)", "The command overwrites fields of existing feature with remote data"
    assert "3 features found" in out.getvalue(), "The command lists the total count of features returned by the request"
    assert "1 synced from source" in out.getvalue(), "The command indicates the total count of features affected"
    assert "1 newly created" in out.getvalue(), "The command indicates the total count of new features recorded"
