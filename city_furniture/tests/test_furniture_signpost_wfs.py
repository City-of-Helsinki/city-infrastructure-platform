import pytest
from rest_framework import status

from city_furniture.tests.factories import get_furniture_signpost_real, get_wfs_url
from traffic_control.tests.factories import get_api_client


@pytest.mark.django_db
def test__wfs_furniture_signpost_real__xml():
    client = get_api_client()
    get_furniture_signpost_real()

    response = client.get(get_wfs_url(model_name="furnituresignpostreal", output_format="application/gml+xml"))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test__wfs_furniture_signpost_real__geojson():
    client = get_api_client()
    get_furniture_signpost_real()

    response = client.get(get_wfs_url(model_name="furnituresignpostreal", output_format="geojson"))
    assert response.status_code == status.HTTP_200_OK
