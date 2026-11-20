"""Copies unexpired sessions from django_session to users_usersession so that nobody is logged out.

The session keys and parsing are inlined so that this migration does not depend on code that may change later.
"""

import uuid
from typing import Any, Optional

from django.apps.registry import Apps
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.utils import timezone

BATCH_SIZE = 1000
AUTH_USER_ID_KEY = "_auth_user_id"


def _user_id(data: dict[str, Any], existing_user_ids: set[uuid.UUID]) -> Optional[uuid.UUID]:
    """Reads the id of an existing user from session data.

    Args:
        data (dict[str, Any]): The decoded session data.
        existing_user_ids (set[uuid.UUID]): Ids of the active users in the database.

    Returns:
        Optional[uuid.UUID]: The user id, or None if missing, malformed or not an active user.
    """
    try:
        user_id = uuid.UUID(str(data[AUTH_USER_ID_KEY]))
    except (KeyError, ValueError):
        return None
    return user_id if user_id in existing_user_ids else None


def copy_sessions(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Copies unexpired sessions and links them to their users.

    Args:
        apps (Apps): The historical app registry.
        schema_editor (BaseDatabaseSchemaEditor): The schema editor.
    """
    Session = apps.get_model("sessions", "Session")
    UserSession = apps.get_model("users", "UserSession")
    User = apps.get_model("users", "User")
    decoder = DBStore()
    # Sessions of inactive users are not linked, so they cannot become usable again if the user is reactivated
    existing_user_ids = set(User.objects.filter(is_active=True).values_list("id", flat=True))
    batch = []
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator(chunk_size=BATCH_SIZE):
        # decode() returns {} for data that cannot be decoded, such as data signed with an old SECRET_KEY
        data = decoder.decode(session.session_data)
        if AUTH_USER_ID_KEY in data and _user_id(data, existing_user_ids) is None:
            continue  # session of a deleted or inactive user, which would only fail to authenticate
        batch.append(
            UserSession(
                session_key=session.session_key,
                session_data=session.session_data,
                expire_date=session.expire_date,
                # Sessions created before this change have no user agent or login time to copy.
                user_id=_user_id(data, existing_user_ids),
            )
        )
        if len(batch) >= BATCH_SIZE:
            UserSession.objects.bulk_create(batch, ignore_conflicts=True)
            batch = []
    UserSession.objects.bulk_create(batch, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("sessions", "0001_initial"),
        ("users", "0012_usersession"),
    ]

    operations = [
        migrations.RunPython(copy_sessions, migrations.RunPython.noop),
    ]
