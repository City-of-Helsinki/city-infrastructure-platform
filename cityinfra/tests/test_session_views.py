"""Tests for the session management admin views."""

import uuid
from typing import Callable

import pytest
from django.contrib.auth import SESSION_KEY
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from rest_framework.authtoken.models import Token

from traffic_control.tests.factories import UserFactory
from users.models import User, UserSession
from users.sessions import session_public_id

FIREFOX_WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"


@pytest.fixture(autouse=True)
def english(settings: SettingsWrapper) -> None:
    """Uses English so that the tests can check page texts.

    Args:
        settings (SettingsWrapper): The pytest-django settings fixture.
    """
    settings.LANGUAGE_CODE = "en"


@pytest.fixture
def staff_client(client: Client) -> Client:
    """Returns a test client logged in as a staff user.

    Args:
        client (Client): Django test client.

    Returns:
        Client: The logged-in client.
    """
    client.force_login(UserFactory(is_staff=True))
    return client


@pytest.fixture
def superuser_client(client: Client) -> Client:
    """Returns a test client logged in as a superuser.

    Args:
        client (Client): Django test client.

    Returns:
        Client: The logged-in client.
    """
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    return client


def _logged_in_user(client: Client) -> User:
    """Returns the user that the test client is logged in as.

    Args:
        client (Client): The logged-in test client.

    Returns:
        User: The logged-in user.
    """
    return User.objects.get(pk=client.session[SESSION_KEY])


def _messages(response: HttpResponse) -> list[str]:
    """Returns the texts of the messages added during the request.

    Args:
        response (HttpResponse): The test client response.

    Returns:
        list[str]: The message texts.
    """
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.mark.django_db
def test_my_account_shows_active_session_count(staff_client: Client, make_session: Callable[..., str]) -> None:
    make_session(_logged_in_user(staff_client))

    response = staff_client.get(reverse("my-account"))

    assert response.status_code == 200
    assert response.context["active_session_count"] == 2
    assert reverse("my-sessions") in response.content.decode()
    assert reverse("all-user-sessions") not in response.content.decode()


@pytest.mark.django_db
def test_my_account_links_superuser_to_all_sessions(superuser_client: Client) -> None:
    response = superuser_client.get(reverse("my-account"))

    assert reverse("all-user-sessions") in response.content.decode()


@pytest.mark.django_db
def test_my_sessions_marks_current_session_and_hides_its_terminate_button(
    staff_client: Client, make_session: Callable[..., str]
) -> None:
    other_key = make_session(_logged_in_user(staff_client), FIREFOX_WINDOWS)
    current_key = staff_client.session.session_key

    response = staff_client.get(reverse("my-sessions"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "This browser (current session)" in content
    assert "Firefox / Windows" in content
    assert session_public_id(other_key) in content
    assert session_public_id(current_key) not in content
    assert current_key not in content
    assert other_key not in content


@pytest.mark.django_db
def test_my_sessions_uses_session_stylesheet(staff_client: Client) -> None:
    response = staff_client.get(reverse("my-sessions"))

    content = response.content.decode()
    assert "cityinfra/css/user_sessions.css" in content


@pytest.mark.django_db
def test_my_sessions_terminates_other_session(staff_client: Client, make_session: Callable[..., str]) -> None:
    other_key = make_session(_logged_in_user(staff_client))

    response = staff_client.post(
        reverse("my-sessions"), {"action": "terminate", "session_id": session_public_id(other_key)}
    )

    assert response.status_code == 302
    assert not UserSession.objects.filter(session_key=other_key).exists()
    assert UserSession.objects.filter(session_key=staff_client.session.session_key).exists()


@pytest.mark.django_db
def test_my_sessions_does_not_terminate_current_session(staff_client: Client) -> None:
    current_key = staff_client.session.session_key

    staff_client.post(reverse("my-sessions"), {"action": "terminate", "session_id": session_public_id(current_key)})

    assert UserSession.objects.filter(session_key=current_key).exists()


@pytest.mark.django_db
def test_my_sessions_terminates_all_other_sessions(staff_client: Client, make_session: Callable[..., str]) -> None:
    user = _logged_in_user(staff_client)
    make_session(user)
    make_session(user)
    other_users_key = make_session(UserFactory())

    staff_client.post(reverse("my-sessions"), {"action": "terminate_others"})

    remaining = set(UserSession.objects.values_list("session_key", flat=True))
    assert remaining == {staff_client.session.session_key, other_users_key}


@pytest.mark.django_db
def test_my_sessions_cannot_terminate_another_users_session(
    staff_client: Client, make_session: Callable[..., str]
) -> None:
    other_users_key = make_session(UserFactory())

    staff_client.post(reverse("my-sessions"), {"action": "terminate", "session_id": session_public_id(other_users_key)})

    assert UserSession.objects.filter(session_key=other_users_key).exists()


@pytest.mark.django_db
def test_my_sessions_requires_staff(client: Client) -> None:
    client.force_login(UserFactory(is_staff=False))

    response = client.get(reverse("my-sessions"))

    assert response.status_code == 302


@pytest.mark.parametrize("url_name", ["all-user-sessions", "user-sessions"])
@pytest.mark.django_db
def test_superuser_session_pages_reject_staff_user(staff_client: Client, url_name: str) -> None:
    kwargs = {"user_id": UserFactory().pk} if url_name == "user-sessions" else {}

    response = staff_client.get(reverse(url_name, kwargs=kwargs))

    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_post_to_user_sessions_rejects_staff_user(
    staff_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory()
    target_key = make_session(target)

    response = staff_client.post(
        reverse("user-sessions", kwargs={"user_id": target.pk}), {"action": "terminate_others"}
    )

    assert response.status_code == 403
    assert UserSession.objects.filter(session_key=target_key).exists()


@pytest.mark.django_db
def test_all_user_sessions_lists_users_with_active_sessions(
    superuser_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory(username="session_owner")
    make_session(target)
    make_session(target)
    UserFactory(username="no_sessions")

    response = superuser_client.get(reverse("all-user-sessions"))

    counts = {user.username: user.active_session_count for user in response.context["users_with_sessions"]}
    assert counts["session_owner"] == 2
    assert "no_sessions" not in counts
    assert reverse("user-sessions", kwargs={"user_id": target.pk}) in response.content.decode()


@pytest.mark.django_db
def test_superuser_terminates_another_users_sessions(
    superuser_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory()
    first_key = make_session(target)
    second_key = make_session(target)
    url = reverse("user-sessions", kwargs={"user_id": target.pk})

    superuser_client.post(url, {"action": "terminate", "session_id": session_public_id(first_key)})
    assert list(UserSession.objects.filter(user=target).values_list("session_key", flat=True)) == [second_key]

    superuser_client.post(url, {"action": "terminate_others"})
    assert not UserSession.objects.filter(user=target).exists()
    assert UserSession.objects.filter(session_key=superuser_client.session.session_key).exists()


@pytest.mark.django_db
def test_terminated_session_is_logged_out(client: Client) -> None:
    user = UserFactory(is_staff=True)
    client.force_login(user)
    other_client = Client()
    other_client.force_login(user)

    client.post(
        reverse("my-sessions"),
        {"action": "terminate", "session_id": session_public_id(other_client.session.session_key)},
    )

    assert other_client.get(reverse("my-account")).status_code == 302


@pytest.mark.django_db
def test_terminating_a_session_shows_success_message(staff_client: Client, make_session: Callable[..., str]) -> None:
    other_key = make_session(_logged_in_user(staff_client))

    response = staff_client.post(
        reverse("my-sessions"), {"action": "terminate", "session_id": session_public_id(other_key)}
    )

    assert _messages(response) == ["The session was terminated."]


@pytest.mark.django_db
def test_terminating_unknown_session_shows_warning(staff_client: Client) -> None:
    response = staff_client.post(reverse("my-sessions"), {"action": "terminate", "session_id": "unknown"})

    assert _messages(response) == ["The session was not found. It may already have ended."]


@pytest.mark.django_db
def test_terminating_other_sessions_shows_count(staff_client: Client, make_session: Callable[..., str]) -> None:
    user = _logged_in_user(staff_client)
    make_session(user)
    make_session(user)

    response = staff_client.post(reverse("my-sessions"), {"action": "terminate_others"})

    assert _messages(response) == ["2 sessions were terminated."]


@pytest.mark.django_db
def test_user_sessions_returns_404_for_unknown_user(superuser_client: Client) -> None:
    response = superuser_client.get(reverse("user-sessions", kwargs={"user_id": uuid.uuid4()}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_sessions_of_another_user_uses_texts_for_other_users(
    superuser_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory()
    make_session(target)

    response = superuser_client.get(reverse("user-sessions", kwargs={"user_id": target.pk}))

    content = response.content.decode()
    assert "Terminate all sessions of this user?" in content
    assert "Terminate all sessions except the one you are using now?" not in content
    assert "The session of the browser you are using now is highlighted" not in content
    assert "This browser (current session)" not in content


@pytest.mark.django_db
def test_my_sessions_uses_texts_for_own_sessions(staff_client: Client, make_session: Callable[..., str]) -> None:
    make_session(_logged_in_user(staff_client))

    response = staff_client.get(reverse("my-sessions"))

    content = response.content.decode()
    assert "Terminate all sessions except the one you are using now?" in content
    assert "The session of the browser you are using now is highlighted" in content


@pytest.mark.django_db
def test_terminating_requires_session_authentication(client: Client, make_session: Callable[..., str]) -> None:
    user = UserFactory(is_staff=True)
    session_key = make_session(user)
    token = Token.objects.create(user=user)  # no factory exists for DRF tokens

    response = client.post(
        reverse("my-sessions"), {"action": "terminate_others"}, HTTP_AUTHORIZATION=f"Token {token.key}"
    )

    assert response.status_code == 403
    assert UserSession.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_terminating_with_token_and_anonymous_session_is_rejected(
    client: Client, make_session: Callable[..., str]
) -> None:
    user = UserFactory(is_staff=True)
    session_key = make_session(user)
    token = Token.objects.create(user=user)  # no factory exists for DRF tokens
    anonymous_session = client.session
    anonymous_session["foo"] = "bar"
    anonymous_session.save()

    response = client.post(
        reverse("my-sessions"), {"action": "terminate_others"}, HTTP_AUTHORIZATION=f"Token {token.key}"
    )

    assert response.status_code == 403
    assert UserSession.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_user_delete_page_does_not_show_session_keys(
    superuser_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory()
    session_key = make_session(target)

    response = superuser_client.get(reverse("admin:users_user_delete", args=[target.pk]))

    assert response.status_code == 200
    assert session_key not in response.content.decode()


@pytest.mark.django_db
def test_user_change_page_relations_table_does_not_list_sessions(
    superuser_client: Client, make_session: Callable[..., str]
) -> None:
    target = UserFactory()
    make_session(target)

    response = superuser_client.get(reverse("admin:users_user_change", args=[target.pk]))

    assert response.status_code == 200
    assert "<td>User Session</td>" not in response.content.decode()
