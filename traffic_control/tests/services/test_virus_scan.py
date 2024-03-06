import pytest
import requests_mock
from django.test import override_settings

from traffic_control.services.virus_scan import clam_av_scan, get_clam_av_scan_url

DUMMY_CLAMAV_URL = "https://test"


@pytest.fixture
def mock_api():
    with requests_mock.Mocker() as m:
        yield m


@override_settings(CLAMAV_BASE_URL=DUMMY_CLAMAV_URL)
def test_virus_scan_not_200(mock_api):
    mock_api.post(get_clam_av_scan_url("v1"), status_code=404, json={})

    ret = clam_av_scan([])
    assert ret["status_code"] == 404
    assert ret["errors"] == [{"detail": "Status code not 200", "viruses": ["ClamAV response not OK"]}]


@override_settings(CLAMAV_URL=DUMMY_CLAMAV_URL)
@pytest.mark.parametrize(
    "fake_response",
    [
        {
            "data": {
                "result": [
                    {"is_infected": True, "name": "Infected1", "viruses": ["streptokokki", "pneumokokki"]},
                    {"is_infected": False, "name": "Ok", "viruses": []},
                    {"is_infected": True, "name": "Infected2", "viruses": ["koli", "korona"]},
                ]
            }
        }
    ],
)
def test_virus_scan(mock_api, fake_response):
    mock_api.post(get_clam_av_scan_url("v1"), status_code=200, json=fake_response)

    ret = clam_av_scan([])
    assert ret["status_code"] == 200
    assert ret["errors"] == [
        {"detail": "Infected1 is infected", "viruses": ["streptokokki", "pneumokokki"]},
        {"detail": "Infected2 is infected", "viruses": ["koli", "korona"]},
    ]
