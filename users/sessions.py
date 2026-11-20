"""Listing and terminating users' login sessions."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone
from django.utils.crypto import salted_hmac

from users.models import User, UserSession

logger = logging.getLogger(__name__)

_HMAC_SALT = "users.sessions.session_public_id"

# Checked in order: Edge and Opera user agents also contain "Chrome", and Chrome's also contains "Safari".
_BROWSERS = (
    ("Edg/", "Edge"),
    ("OPR/", "Opera"),
    ("Firefox/", "Firefox"),
    ("Chrome/", "Chrome"),
    ("Safari/", "Safari"),
)
# Android and iOS user agents also contain "Linux" and "Mac OS X".
_OPERATING_SYSTEMS = (
    ("Android", "Android"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("Windows", "Windows"),
    ("Mac OS X", "macOS"),
    ("Linux", "Linux"),
)


@dataclass(frozen=True)
class SessionInfo:
    """Displayable details of one session. Does not contain the secret session key.

    Attributes:
        public_id (str): A non-secret identifier for the session, used in forms.
        description (str): A short description of the browser and operating system.
        user_agent (str): The full user agent string.
        logged_in_at (Optional[datetime]): When the user logged in, if known.
        expire_date (datetime): When the session expires.
        is_current (bool): Whether this is the session of the browser making the request.
    """

    public_id: str
    description: str
    user_agent: str
    logged_in_at: Optional[datetime]
    expire_date: datetime
    is_current: bool


def session_public_id(session_key: str) -> str:
    """Derives a non-secret identifier for a session.

    The session key is a credential, so it is never put into pages or URLs. The identifier is an HMAC of
    the key, so the key cannot be derived from it.

    Args:
        session_key (str): The secret session key.

    Returns:
        str: The public identifier.
    """
    return salted_hmac(_HMAC_SALT, session_key, algorithm="sha256").hexdigest()[:32]


def describe_user_agent(user_agent: str) -> str:
    """Builds a short description such as "Firefox on Windows" from a user agent string.

    Args:
        user_agent (str): The user agent string.

    Returns:
        str: The description, or an empty string if the user agent is unknown.
    """
    browser = next((name for token, name in _BROWSERS if token in user_agent), "")
    operating_system = next((name for token, name in _OPERATING_SYSTEMS if token in user_agent), "")
    if browser and operating_system:
        return f"{browser} / {operating_system}"
    return browser or operating_system


def get_active_sessions(user: User) -> QuerySet[UserSession]:
    """Returns the user's unexpired sessions.

    Args:
        user (User): The user.

    Returns:
        QuerySet[UserSession]: The sessions.
    """
    return UserSession.objects.filter(user=user, expire_date__gt=timezone.now())


def count_active_sessions(user: User) -> int:
    """Counts the user's unexpired sessions.

    Args:
        user (User): The user.

    Returns:
        int: The number of sessions.
    """
    return get_active_sessions(user).count()


def list_sessions(user: User, current_session_key: Optional[str]) -> list[SessionInfo]:
    """Lists the user's unexpired sessions, current session first, then newest login first.

    Args:
        user (User): The user whose sessions are listed.
        current_session_key (Optional[str]): The session key of the browser making the request.

    Returns:
        list[SessionInfo]: The sessions.
    """
    infos = [
        SessionInfo(
            public_id=session_public_id(session.session_key),
            description=describe_user_agent(session.user_agent),
            user_agent=session.user_agent,
            logged_in_at=session.logged_in_at,
            expire_date=session.expire_date,
            is_current=session.session_key == current_session_key,
        )
        for session in get_active_sessions(user).defer("session_data")
    ]
    oldest = datetime.min.replace(tzinfo=timezone.get_current_timezone())
    infos.sort(key=lambda info: info.logged_in_at or oldest, reverse=True)
    infos.sort(key=lambda info: not info.is_current)
    return infos


def terminate_session(user: User, public_id: str, current_session_key: Optional[str], terminated_by: User) -> bool:
    """Terminates one of the user's sessions. The current session is never terminated.

    Args:
        user (User): The user whose session is terminated.
        public_id (str): The public identifier of the session.
        current_session_key (Optional[str]): The session key of the browser making the request.
        terminated_by (User): The user who requested the termination.

    Returns:
        bool: True if a session was terminated.
    """
    sessions = get_active_sessions(user).exclude(session_key=current_session_key or "")
    keys = [key for key in sessions.values_list("session_key", flat=True) if session_public_id(key) == public_id]
    deleted, _ = UserSession.objects.filter(session_key__in=keys).delete()
    if deleted:
        logger.info("User %s terminated a session of user %s", terminated_by.pk, user.pk)
    return bool(deleted)


def terminate_other_sessions(user: User, current_session_key: Optional[str], terminated_by: User) -> int:
    """Terminates all of the user's sessions except the current one.

    Args:
        user (User): The user whose sessions are terminated.
        current_session_key (Optional[str]): The session key of the browser making the request.
        terminated_by (User): The user who requested the termination.

    Returns:
        int: The number of terminated sessions.
    """
    deleted, _ = get_active_sessions(user).exclude(session_key=current_session_key or "").delete()
    if deleted:
        logger.info("User %s terminated %d sessions of user %s", terminated_by.pk, deleted, user.pk)
    return deleted
