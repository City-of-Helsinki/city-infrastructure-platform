"""Tests for the django-helusers admin login flow.

Since django-helusers 1.3.0 the login initiation uses POST instead of GET, for
compatibility with social-auth-app-django 6.x which no longer allows GET.
"""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_helusers_login_post_redirects_to_social_begin(client: Client) -> None:
    """
    Test that POSTing to the helusers login view starts the OIDC login.

    Args:
        client (Client): Django test client.

    Returns:
        None
    """
    response = client.post(reverse("helusers:auth_login"), data={"next": "/admin/"})

    assert response.status_code == 307
    assert response.url == f"{reverse('social:begin', kwargs={'backend': 'tunnistamo'})}?next=%2Fadmin%2F"


@pytest.mark.django_db
def test_helusers_login_get_is_not_allowed(client: Client) -> None:
    """
    Test that the helusers login view rejects GET requests.

    Args:
        client (Client): Django test client.

    Returns:
        None
    """
    response = client.get(reverse("helusers:auth_login"), data={"next": "/admin/"})

    assert response.status_code == 405
