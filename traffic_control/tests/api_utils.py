from django.urls import reverse

from traffic_control.tests.factories import get_api_client, get_user


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


def do_illegal_geometry_test(endpoint, data, expected_non_field_errors):
    client = get_api_client(user=get_user(admin=True))

    response = client.post(reverse(endpoint), data=data)
    assert response.status_code == 400
    assert response.json().get("non_field_errors") == expected_non_field_errors
