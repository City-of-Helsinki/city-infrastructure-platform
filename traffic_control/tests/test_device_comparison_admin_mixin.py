from http import HTTPStatus

import pytest
from django.urls import reverse

from traffic_control.tests.factories import get_user


@pytest.mark.parametrize(
    "url_name",
    (
        "admin:traffic_control_additionalsignreal_change",
        "admin:traffic_control_barrierreal_change",
        "admin:traffic_control_mountreal_change",
        "admin:traffic_control_roadmarkingreal_change",
        "admin:traffic_control_signpostreal_change",
        "admin:traffic_control_trafficlightreal_change",
        "admin:traffic_control_trafficsignreal_change",
        "admin:city_furniture_furnituresignpostreal_change",
    ),
)
@pytest.mark.django_db
def test_device_comparison_admin_mixin_object_does_not_exit(client, url_name):
    client.force_login(get_user(admin=True))

    response = client.get(reverse(url_name, kwargs={"object_id": "doesnotexist"}), follow=True)

    assert response.status_code == HTTPStatus.OK
    assert response.context["LANGUAGE_CODE"] == "en"
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert "with ID “doesnotexist” doesn’t exist. Perhaps it was deleted?" in messages[0].message
