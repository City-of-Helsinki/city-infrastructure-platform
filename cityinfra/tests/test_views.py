import pytest
from django.urls import reverse


@pytest.mark.django_db
def test__health_check(client, settings):
    env_name = "envname"
    version = "abc123"
    settings.ENVIRONMENT_NAME = env_name
    settings.VERSION = version

    url = reverse("health-check")
    response = client.get(url)
    response_json = response.json()

    assert response.status_code == 200
    assert response_json.get("status") == "OK"
    assert response_json.get("service") == "city-infrastructure-platform"
    assert response_json.get("environment") == env_name
    assert response_json.get("version") == version
