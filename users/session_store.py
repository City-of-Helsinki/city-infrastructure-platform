"""Database session backend that links sessions to users.

Enable it with ``SESSION_ENGINE = "users.session_store"``.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.utils.dateparse import parse_datetime

from users.models import User, UserSession

USER_AGENT_SESSION_KEY = "_user_agent"
LOGGED_IN_AT_SESSION_KEY = "_logged_in_at"
USER_AGENT_MAX_LENGTH = UserSession._meta.get_field("user_agent").max_length


class SessionStore(DBStore):
    """Session store that saves sessions to ``UserSession`` with the owning user."""

    @classmethod
    def get_model_class(cls) -> type[UserSession]:
        """Returns the model used to store sessions.

        Returns:
            type[UserSession]: The session model.
        """
        return UserSession

    def create_model_instance(self, data: dict[str, Any]) -> UserSession:
        """Builds a session model instance and copies the user details from the session data.

        Args:
            data (dict[str, Any]): The session data.

        Returns:
            UserSession: The unsaved session instance.
        """
        user_id = user_id_from_session_data(data)
        if user_id is not None and not User.objects.filter(pk=user_id).exists():
            user_id = None
        return _add_user_details(super().create_model_instance(data), data, user_id)

    async def acreate_model_instance(self, data: dict[str, Any]) -> UserSession:
        """Async version of ``create_model_instance``.

        Args:
            data (dict[str, Any]): The session data.

        Returns:
            UserSession: The unsaved session instance.
        """
        user_id = user_id_from_session_data(data)
        if user_id is not None and not await User.objects.filter(pk=user_id).aexists():
            user_id = None
        return _add_user_details(await super().acreate_model_instance(data), data, user_id)


def _add_user_details(obj: UserSession, data: dict[str, Any], user_id: Optional[uuid.UUID]) -> UserSession:
    """Copies the user, user agent and login time to the session instance.

    The user is linked only if it exists. A session can still be saved after its user has been deleted, for
    example by a request that was in progress, and linking it to the missing user would fail on the foreign
    key when the transaction commits.

    Args:
        obj (UserSession): The unsaved session instance.
        data (dict[str, Any]): The session data.
        user_id (Optional[uuid.UUID]): The id of the existing user the session belongs to, or None.

    Returns:
        UserSession: The same instance, with the user details set.
    """
    obj.user_id = user_id
    obj.user_agent = str(data.get(USER_AGENT_SESSION_KEY, ""))[:USER_AGENT_MAX_LENGTH]
    obj.logged_in_at = _parse_logged_in_at(data.get(LOGGED_IN_AT_SESSION_KEY))
    return obj


def user_id_from_session_data(data: dict[str, Any]) -> Optional[uuid.UUID]:
    """Reads the logged-in user's id from session data.

    Args:
        data (dict[str, Any]): The session data.

    Returns:
        Optional[uuid.UUID]: The user id, or None for an anonymous or malformed session.
    """
    try:
        return uuid.UUID(str(data[SESSION_KEY]))
    except (KeyError, ValueError):
        return None


def _parse_logged_in_at(value: Any) -> Optional[datetime]:
    """Parses the stored login time.

    Args:
        value (Any): The ISO 8601 string from the session data, or None.

    Returns:
        Optional[datetime]: The parsed timestamp, or None if missing or invalid.
    """
    if not isinstance(value, str):
        return None
    try:
        return parse_datetime(value)
    except ValueError:
        return None
