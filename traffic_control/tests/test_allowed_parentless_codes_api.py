"""Tests for allowed_parentless_additional_sign_codes API endpoint."""
import pytest
from django.urls import reverse
from rest_framework import status

from traffic_control.constants import TICKET_MACHINE_CODES
from traffic_control.tests.factories import get_api_client, get_user


@pytest.mark.django_db
def test_allowed_parentless_additional_sign_codes_returns_ticket_machine_codes() -> None:
    """
    Test that the API endpoint returns the correct list of ticket machine codes.

    Returns:
        None
    """
    client = get_api_client(user=get_user())
    url = reverse("allowed-parentless-additional-sign-codes")

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert "codes" in response_data
    assert response_data["codes"] == TICKET_MACHINE_CODES


@pytest.mark.django_db
def test_allowed_parentless_additional_sign_codes_contains_expected_codes() -> None:
    """
    Test that the API response contains all expected ticket machine codes.

    Returns:
        None
    """
    client = get_api_client(user=get_user())
    url = reverse("allowed-parentless-additional-sign-codes")

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    codes = response.json()["codes"]

    # Check for new codes
    assert "H20.91" in codes
    assert "H20.92" in codes
    assert "H20.93" in codes

    # Check for legacy codes
    assert "8591" in codes
    assert "8592" in codes
    assert "8593" in codes


@pytest.mark.django_db
def test_allowed_parentless_additional_sign_codes_is_read_only() -> None:
    """
    Test that the API endpoint only accepts GET requests for authenticated users.

    Returns:
        None
    """
    client = get_api_client(user=get_user())
    url = reverse("allowed-parentless-additional-sign-codes")

    # POST should not be allowed
    response = client.post(url, data={})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # PUT should not be allowed
    response = client.put(url, data={})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # DELETE should not be allowed
    response = client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # PATCH should not be allowed
    response = client.patch(url, data={})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_allowed_parentless_additional_sign_codes_requires_authentication() -> None:
    """
    Test that the API endpoint requires authentication.

    Returns:
        None
    """
    client = get_api_client(user=None)  # Unauthenticated
    url = reverse("allowed-parentless-additional-sign-codes")

    response = client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
