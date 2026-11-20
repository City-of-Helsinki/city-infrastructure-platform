"""Tests for the account deactivated page shown to deactivated AD/Tunnistamo users (LIIK-1041)."""

from unittest.mock import patch

import pytest
from django.conf import settings as django_settings
from django.test import Client
from django.urls import resolve, reverse
from helusers.tunnistamo_oidc import TunnistamoOIDCAuth
from pytest_django.fixtures import SettingsWrapper

from cityinfra.views import AccountDeactivatedView
from traffic_control.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def settings(settings: SettingsWrapper) -> SettingsWrapper:
    """Use English so that the tests can check page texts.

    Args:
        settings (SettingsWrapper): The pytest-django settings fixture.

    Returns:
        SettingsWrapper: The modified settings fixture.
    """
    settings.LANGUAGE_CODE = "en"
    return settings


def test__account_deactivated__url_resolves_to_view() -> None:
    """Checks that the account deactivated URL resolves to `AccountDeactivatedView`."""
    url = reverse("account-deactivated")

    assert url == "/account-deactivated/"
    assert resolve(url).func.view_class is AccountDeactivatedView


def test__social_auth_inactive_user_url__points_to_account_deactivated_page() -> None:
    """Checks that python-social-auth redirects inactive users to the account deactivated page."""
    assert django_settings.SOCIAL_AUTH_INACTIVE_USER_URL == reverse("account-deactivated")


@pytest.mark.django_db
def test__login_url__points_to_existing_admin_login_page(client: Client) -> None:
    """Checks that `LOGIN_URL` leads to the working admin login page.

    Without `LOGIN_URL`, Django defaults to the non-existent `/accounts/login/`. Admin lives under
    `i18n_patterns`, so the unprefixed URL redirects to the language-prefixed login page.

    Args:
        client (Client): The Django test client.
    """
    assert django_settings.LOGIN_URL == "/admin/login/"

    response = client.get(django_settings.LOGIN_URL, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse("admin:login")


@pytest.mark.django_db
def test__account_deactivated__anonymous_user_gets_page(client: Client) -> None:
    """Checks that an anonymous user gets the page.

    Args:
        client (Client): The Django test client.
    """
    response = client.get(reverse("account-deactivated"))

    assert response.status_code == 200
    assert "account_deactivated.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test__account_deactivated__page_content(client: Client) -> None:
    """Checks that the page shows the messages, the login link and the stylesheet.

    Args:
        client (Client): The Django test client.
    """
    response = client.get(reverse("account-deactivated"))
    content = response.content.decode()

    assert "Account Deactivated" in content
    assert (
        "Your account has been deactivated, likely due to prolonged inactivity or due to a manual deactivation "
        "by a system administrator."
    ) in content
    assert "please contact your system administrator to reactivate your account" in content
    assert f'href="{reverse("admin:login")}"' in content
    assert "Back to login page" in content
    assert "cityinfra/css/status_page.css" in content


@pytest.mark.django_db
def test__account_deactivated__authenticated_user_gets_page(client: Client) -> None:
    """Checks that a logged-in user can also open the page.

    Args:
        client (Client): The Django test client.
    """
    client.force_login(UserFactory())

    response = client.get(reverse("account-deactivated"))

    assert response.status_code == 200


@pytest.mark.django_db
def test__social_auth_complete__inactive_user_is_redirected_to_account_deactivated_page(client: Client) -> None:
    """Checks that successful AD/Tunnistamo authentication of a deactivated user lands on the deactivated page.

    The deactivated user must not be logged in.

    Args:
        client (Client): The Django test client.
    """
    user = UserFactory(is_active=False)

    with patch.object(TunnistamoOIDCAuth, "complete", return_value=user):
        response = client.get(reverse("social:complete", args=[TunnistamoOIDCAuth.name]))

    assert response.status_code == 302
    assert response.url == reverse("account-deactivated")
    assert "_auth_user_id" not in client.session

    followed = client.get(response.url)
    assert followed.status_code == 200
    assert "account_deactivated.html" in [t.name for t in followed.templates]


@pytest.mark.django_db
def test__social_auth_complete__active_user_is_logged_in_and_redirected_to_admin(client: Client) -> None:
    """Checks that an active AD/Tunnistamo user is logged in and redirected to `LOGIN_REDIRECT_URL`.

    No factory exists for `UserSocialAuth`, so the association is created through the related manager.

    Args:
        client (Client): The Django test client.
    """
    user = UserFactory(is_active=True)
    user.social_user = user.social_auth.create(provider=TunnistamoOIDCAuth.name, uid="test-uid")
    user.is_new = False

    with patch.object(TunnistamoOIDCAuth, "complete", return_value=user):
        response = client.get(reverse("social:complete", args=[TunnistamoOIDCAuth.name]))

    assert response.status_code == 302
    assert response.url == django_settings.LOGIN_REDIRECT_URL
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test__social_auth_complete__failed_authentication_is_redirected_to_admin_login(client: Client) -> None:
    """Checks that failed AD/Tunnistamo authentication redirects to `LOGIN_URL`.

    Args:
        client (Client): The Django test client.
    """
    with patch.object(TunnistamoOIDCAuth, "complete", return_value=None):
        response = client.get(reverse("social:complete", args=[TunnistamoOIDCAuth.name]))

    assert response.status_code == 302
    assert response.url == django_settings.LOGIN_URL
