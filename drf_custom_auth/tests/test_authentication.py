"""Tests for custom DRF authentication classes that update last_api_use."""

import base64
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from drf_custom_auth.authentication import LastApiUseBasicAuthentication, LastApiUseTokenAuthentication
from traffic_control.tests.factories import UserFactory


def _basic_auth_header(username: str, password: str) -> str:
    """Build a Basic auth Authorization header value.

    Args:
        username (str): The username to encode.
        password (str): The password to encode.

    Returns:
        str: A Basic auth header value, e.g. 'Basic dXNlcjpwYXNz'.
    """
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {credentials}"


@pytest.fixture
def user():
    """Create a test user with a known password.

    Returns:
        User: A saved User instance with password 'testpass123'.
    """
    u = UserFactory(username="authtest_user", email="authtest@example.com")
    u.set_password("testpass123")
    u.save()
    return u


@pytest.fixture
def factory():
    """Return a DRF APIRequestFactory.

    Returns:
        APIRequestFactory: A factory for building DRF test requests.
    """
    return APIRequestFactory()


# ---------------------------------------------------------------------------
# LastApiUseBasicAuthentication
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_basic_auth_success_updates_last_api_use(user, factory):
    """Successful basic auth sets last_api_use to today."""
    assert user.last_api_use is None

    request = factory.get("/", HTTP_AUTHORIZATION=_basic_auth_header("authtest_user", "testpass123"))
    auth = LastApiUseBasicAuthentication()
    result = auth.authenticate(request)

    assert result is not None
    assert result[0].pk == user.pk
    user.refresh_from_db()
    assert user.last_api_use == timezone.now().date()


@pytest.mark.django_db
def test_basic_auth_failed_does_not_update_last_api_use(user, factory):
    """Failed basic auth (wrong password) does not update last_api_use."""
    request = factory.get("/", HTTP_AUTHORIZATION=_basic_auth_header("authtest_user", "wrongpassword"))
    auth = LastApiUseBasicAuthentication()

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(request)

    user.refresh_from_db()
    assert user.last_api_use is None


@pytest.mark.django_db
def test_basic_auth_no_header_returns_none(factory):
    """Request without Authorization header returns None (auth not attempted)."""
    request = factory.get("/")
    auth = LastApiUseBasicAuthentication()
    result = auth.authenticate(request)
    assert result is None


@pytest.mark.django_db
def test_basic_auth_no_db_write_when_already_today(user, factory):
    """No extra DB write when last_api_use is already today."""
    today = timezone.now().date()
    user.last_api_use = today
    user.save(update_fields=["last_api_use"])

    request = factory.get("/", HTTP_AUTHORIZATION=_basic_auth_header("authtest_user", "testpass123"))
    auth = LastApiUseBasicAuthentication()

    with patch("drf_custom_auth.authentication.User.objects") as mock_objects:
        result = auth.authenticate(request)
        mock_objects.filter.assert_not_called()

    assert result is not None
    user.refresh_from_db()
    assert user.last_api_use == today


# ---------------------------------------------------------------------------
# LastApiUseTokenAuthentication
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_token_auth_success_updates_last_api_use(user, factory):
    """Successful token auth sets last_api_use to today."""
    assert user.last_api_use is None
    token = Token.objects.create(user=user)

    request = factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
    auth = LastApiUseTokenAuthentication()
    result = auth.authenticate(request)

    assert result is not None
    assert result[0].pk == user.pk
    user.refresh_from_db()
    assert user.last_api_use == timezone.now().date()


@pytest.mark.django_db
def test_token_auth_invalid_token_does_not_update_last_api_use(user, factory):
    """Invalid token does not update last_api_use."""
    request = factory.get("/", HTTP_AUTHORIZATION="Token invalidtoken123")
    auth = LastApiUseTokenAuthentication()

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(request)

    user.refresh_from_db()
    assert user.last_api_use is None


@pytest.mark.django_db
def test_token_auth_no_header_returns_none(factory):
    """Request without Authorization header returns None (auth not attempted)."""
    request = factory.get("/")
    auth = LastApiUseTokenAuthentication()
    result = auth.authenticate(request)
    assert result is None


@pytest.mark.django_db
def test_token_auth_no_db_write_when_already_today(user, factory):
    """No extra DB write when last_api_use is already today."""
    today = timezone.now().date()
    user.last_api_use = today
    user.save(update_fields=["last_api_use"])

    token = Token.objects.create(user=user)
    request = factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
    auth = LastApiUseTokenAuthentication()

    with patch("drf_custom_auth.authentication.User.objects") as mock_objects:
        result = auth.authenticate(request)
        mock_objects.filter.assert_not_called()

    assert result is not None
    user.refresh_from_db()
    assert user.last_api_use == today
