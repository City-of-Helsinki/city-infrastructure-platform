"""Tests for the user session store, the session helpers and the session copy migration."""

import importlib
import uuid
from datetime import timedelta
from typing import Any, Callable, Optional

import pytest
from asgiref.sync import async_to_sync
from django.apps import apps
from django.contrib.auth import login, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.models import Session
from django.test import RequestFactory
from django.utils import timezone

from traffic_control.tests.factories import UserFactory
from users.models import UserSession
from users.session_store import (
    LOGGED_IN_AT_SESSION_KEY,
    SessionStore,
    USER_AGENT_SESSION_KEY,
    user_id_from_session_data,
)
from users.sessions import (
    count_active_sessions,
    describe_user_agent,
    list_sessions,
    session_public_id,
    terminate_other_sessions,
    terminate_session,
)

FIREFOX_WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
EDGE_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1"
)


@pytest.mark.django_db
def test_session_store_links_session_to_user(make_session: Callable[..., str]) -> None:
    user = UserFactory()

    session_key = make_session(user, FIREFOX_WINDOWS)

    stored = UserSession.objects.get(session_key=session_key)
    assert stored.user == user
    assert stored.user_agent == FIREFOX_WINDOWS
    assert stored.logged_in_at is not None


@pytest.mark.django_db
def test_session_store_leaves_anonymous_session_without_user() -> None:
    session = SessionStore()
    session["foo"] = "bar"
    session.create()

    assert UserSession.objects.get(session_key=session.session_key).user is None


@pytest.mark.django_db
def test_session_store_keeps_login_time_when_session_is_saved_again(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    session_key = make_session(user)
    logged_in_at = UserSession.objects.get(session_key=session_key).logged_in_at

    session = SessionStore(session_key=session_key)
    session["foo"] = "bar"
    session.save()

    assert UserSession.objects.get(session_key=session_key).logged_in_at == logged_in_at


@pytest.mark.django_db
def test_login_stores_user_agent_and_login_time(rf: RequestFactory) -> None:
    user = UserFactory()
    request = rf.get("/", HTTP_USER_AGENT=FIREFOX_WINDOWS)
    request.session = SessionStore()

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.save()

    stored = UserSession.objects.get(session_key=request.session.session_key)
    assert stored.user == user
    assert stored.user_agent == FIREFOX_WINDOWS
    assert stored.logged_in_at is not None


@pytest.mark.parametrize(
    "user_agent,expected",
    [
        (FIREFOX_WINDOWS, "Firefox / Windows"),
        (EDGE_WINDOWS, "Edge / Windows"),
        (SAFARI_IPHONE, "Safari / iOS"),
        ("python-requests/2.32", ""),
        ("", ""),
    ],
)
def test_describe_user_agent(user_agent: str, expected: str) -> None:
    assert describe_user_agent(user_agent) == expected


def test_session_public_id_does_not_reveal_session_key() -> None:
    public_id = session_public_id("abc123")

    assert "abc123" not in public_id
    assert public_id == session_public_id("abc123")
    assert public_id != session_public_id("abc124")


@pytest.mark.django_db
def test_count_active_sessions_ignores_expired_and_other_users_sessions(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    make_session(user)
    expired_key = make_session(user)
    UserSession.objects.filter(session_key=expired_key).update(expire_date=timezone.now() - timedelta(minutes=1))
    make_session(UserFactory())

    assert count_active_sessions(user) == 1


@pytest.mark.django_db
def test_list_sessions_puts_current_session_first(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    current_key = make_session(user, FIREFOX_WINDOWS)
    make_session(user, EDGE_WINDOWS)

    sessions = list_sessions(user, current_key)

    assert [session.is_current for session in sessions] == [True, False]
    assert sessions[0].description == "Firefox / Windows"
    assert sessions[0].public_id == session_public_id(current_key)


@pytest.mark.django_db
def test_terminate_session_terminates_the_given_session(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    current_key = make_session(user)
    other_key = make_session(user)

    assert terminate_session(user, session_public_id(other_key), current_key, terminated_by=user)

    assert list(UserSession.objects.values_list("session_key", flat=True)) == [current_key]


@pytest.mark.django_db
def test_terminate_session_does_not_terminate_current_session(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    current_key = make_session(user)

    assert not terminate_session(user, session_public_id(current_key), current_key, terminated_by=user)

    assert UserSession.objects.filter(session_key=current_key).exists()


@pytest.mark.django_db
def test_terminate_session_does_not_terminate_another_users_session(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    other_users_key = make_session(UserFactory())

    assert not terminate_session(user, session_public_id(other_users_key), None, terminated_by=user)

    assert UserSession.objects.filter(session_key=other_users_key).exists()


@pytest.mark.django_db
def test_terminate_other_sessions_keeps_current_and_other_users_sessions(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    current_key = make_session(user)
    make_session(user)
    make_session(user)
    other_users_key = make_session(UserFactory())

    assert terminate_other_sessions(user, current_key, terminated_by=user) == 2

    assert set(UserSession.objects.values_list("session_key", flat=True)) == {current_key, other_users_key}


@pytest.mark.parametrize(
    "data,expected",
    [
        ({SESSION_KEY: "4f1c6a2e-0d3b-4c5e-9a7f-1b2c3d4e5f60"}, uuid.UUID("4f1c6a2e-0d3b-4c5e-9a7f-1b2c3d4e5f60")),
        ({SESSION_KEY: "not-a-uuid"}, None),
        ({SESSION_KEY: 1}, None),
        ({}, None),
    ],
)
def test_user_id_from_session_data(data: dict[str, Any], expected: Optional[uuid.UUID]) -> None:
    assert user_id_from_session_data(data) == expected


@pytest.mark.parametrize("logged_in_at", [None, 123, "not a date", "2026-13-45T00:00:00"])
@pytest.mark.django_db
def test_session_store_ignores_missing_or_invalid_login_time(logged_in_at: Any) -> None:
    session = SessionStore()
    session[LOGGED_IN_AT_SESSION_KEY] = logged_in_at
    session.create()

    assert UserSession.objects.get(session_key=session.session_key).logged_in_at is None


@pytest.mark.django_db
def test_session_store_does_not_link_session_to_missing_user() -> None:
    session = SessionStore()
    session[SESSION_KEY] = "4f1c6a2e-0d3b-4c5e-9a7f-1b2c3d4e5f60"
    session.create()

    assert UserSession.objects.get(session_key=session.session_key).user is None


@pytest.mark.django_db
def test_session_str_does_not_reveal_session_key(make_session: Callable[..., str]) -> None:
    session_key = make_session(UserFactory())

    text = str(UserSession.objects.get(session_key=session_key))

    assert session_key not in text
    assert text == session_public_id(session_key)[:8]


@pytest.mark.django_db
def test_deactivating_user_deletes_their_sessions(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    make_session(user)
    other_users_key = make_session(UserFactory())

    user.is_active = False
    user.save(update_fields=["is_active"])

    assert list(UserSession.objects.values_list("session_key", flat=True)) == [other_users_key]


@pytest.mark.django_db
def test_saving_active_user_keeps_their_sessions(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    session_key = make_session(user)

    user.first_name = "Changed"
    user.save()

    assert UserSession.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_session_store_async_create_links_session_to_user() -> None:
    user = UserFactory()
    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[USER_AGENT_SESSION_KEY] = FIREFOX_WINDOWS
    session[LOGGED_IN_AT_SESSION_KEY] = timezone.now().isoformat()

    async_to_sync(session.acreate)()

    stored = UserSession.objects.get(session_key=session.session_key)
    assert stored.user == user
    assert stored.user_agent == FIREFOX_WINDOWS
    assert stored.logged_in_at is not None


@pytest.mark.django_db
def test_list_sessions_orders_by_newest_login_and_unknown_login_last(make_session: Callable[..., str]) -> None:
    user = UserFactory()
    now = timezone.now()
    unknown_key = make_session(user)
    older_key = make_session(user)
    newer_key = make_session(user)
    current_key = make_session(user)
    UserSession.objects.filter(session_key=unknown_key).update(logged_in_at=None)
    UserSession.objects.filter(session_key=older_key).update(logged_in_at=now - timedelta(days=2))
    UserSession.objects.filter(session_key=newer_key).update(logged_in_at=now - timedelta(days=1))
    UserSession.objects.filter(session_key=current_key).update(logged_in_at=now - timedelta(days=3))

    sessions = list_sessions(user, current_key)

    expected = [current_key, newer_key, older_key, unknown_key]
    assert [session.public_id for session in sessions] == [session_public_id(key) for key in expected]


def _create_old_session(data: dict[str, Any]) -> str:
    """Creates a session in the old django_session table.

    Args:
        data (dict[str, Any]): The session data.

    Returns:
        str: The session key.
    """
    session = DBStore()
    session.update(data)
    session.create()
    return session.session_key


@pytest.mark.django_db
def test_copy_sessions_migration_copies_anonymous_session_without_user() -> None:
    session_key = _create_old_session({"foo": "bar"})
    migration = importlib.import_module("users.migrations.0013_copy_existing_sessions")

    migration.copy_sessions(apps, None)

    copied = UserSession.objects.get()
    assert copied.session_key == session_key
    assert copied.user is None


@pytest.mark.parametrize(
    "user_id",
    [
        "4f1c6a2e-0d3b-4c5e-9a7f-1b2c3d4e5f60",  # user that does not exist
        "not-a-uuid",
        "inactive",
    ],
)
@pytest.mark.django_db
def test_copy_sessions_migration_skips_sessions_without_valid_active_user(user_id: str) -> None:
    if user_id == "inactive":
        user_id = str(UserFactory(is_active=False).pk)
    _create_old_session({SESSION_KEY: user_id})
    migration = importlib.import_module("users.migrations.0013_copy_existing_sessions")

    migration.copy_sessions(apps, None)

    assert not UserSession.objects.exists()


@pytest.mark.django_db
def test_copy_sessions_migration_copies_undecodable_session_without_user() -> None:
    session_key = _create_old_session({"foo": "bar"})
    Session.objects.filter(session_key=session_key).update(session_data="garbage")
    migration = importlib.import_module("users.migrations.0013_copy_existing_sessions")

    migration.copy_sessions(apps, None)

    copied = UserSession.objects.get()
    assert copied.session_key == session_key
    assert copied.session_data == "garbage"
    assert copied.user is None


@pytest.mark.django_db
def test_copy_sessions_migration_copies_unexpired_sessions_with_users() -> None:
    user = UserFactory()
    old_session = DBStore()
    old_session[SESSION_KEY] = str(user.pk)
    old_session.create()
    expired_session = DBStore()
    expired_session[SESSION_KEY] = str(user.pk)
    expired_session.create()
    Session.objects.filter(session_key=expired_session.session_key).update(
        expire_date=timezone.now() - timedelta(minutes=1)
    )
    migration = importlib.import_module("users.migrations.0013_copy_existing_sessions")

    migration.copy_sessions(apps, None)

    copied = UserSession.objects.get()
    assert copied.session_key == old_session.session_key
    assert copied.user == user
    assert SessionStore(session_key=copied.session_key).load()[SESSION_KEY] == str(user.pk)
