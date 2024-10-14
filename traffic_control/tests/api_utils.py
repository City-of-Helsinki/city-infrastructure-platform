from django.urls import reverse

from traffic_control.tests.factories import get_api_client


def do_filtering_test(factory, endpoint, field_name, value, second_value):
    client = get_api_client()

    factory(**{field_name: value})
    factory(**{field_name: second_value})

    response = client.get(reverse(endpoint), data={field_name: value})
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get(reverse(endpoint))
    assert response.status_code == 200
    assert response.json()["count"] == 2
