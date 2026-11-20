"""Signal handlers for the users app."""

from typing import Optional

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils import timezone

from users.models import User, UserSession
from users.session_store import LOGGED_IN_AT_SESSION_KEY, USER_AGENT_MAX_LENGTH, USER_AGENT_SESSION_KEY


@receiver(user_logged_in)
def store_session_login_details(sender: type, request: HttpRequest | None, user: User, **kwargs: dict) -> None:
    """Stores the browser's user agent and the login time in the new session.

    The values let users recognise their sessions on the session management pages.

    Args:
        sender (type): The class of the user that logged in.
        request (HttpRequest | None): The login request, if there is one.
        user (User): The user that logged in.
        **kwargs (dict): Additional keyword arguments from the signal.
    """
    session = getattr(request, "session", None)
    if session is None:
        return
    session[USER_AGENT_SESSION_KEY] = request.META.get("HTTP_USER_AGENT", "")[:USER_AGENT_MAX_LENGTH]
    session[LOGGED_IN_AT_SESSION_KEY] = timezone.now().isoformat()


@receiver(post_save, sender=User)
def delete_deactivation_status_on_activity(
    sender: type[User], instance: User, update_fields: Optional[set[str]], **kwargs: dict
) -> None:
    """
    Delete UserDeactivationStatus when user becomes active again.

    This signal handler removes the deactivation status record when:
    - User's last_login, last_api_use, or reactivated_at timestamp is updated (renewed activity)
    - User's is_active field is set to True (manual reactivation by admin)

    When is_active is set to True without reactivated_at being set, this signal
    automatically sets the reactivated_at timestamp.

    Args:
        sender (type[User]): The User model class.
        instance (User): The User instance being saved.
        update_fields (Optional[set[str]]): Set of field names being updated, or None.
        **kwargs (dict): Additional keyword arguments from the signal.
    """
    if update_fields is not None:
        activity_fields = {"last_login", "last_api_use", "reactivated_at"}

        # Check if user is being reactivated (is_active set to True)
        if "is_active" in update_fields and instance.is_active:
            # Set reactivated_at if not already set in this save
            if "reactivated_at" not in update_fields and instance.reactivated_at is None:
                instance.reactivated_at = timezone.now()
                # Update the database with reactivated_at
                # Use update() to avoid triggering this signal again
                User.objects.filter(pk=instance.pk).update(reactivated_at=instance.reactivated_at)

            # Delete deactivation status
            if hasattr(instance, "deactivation_status"):
                instance.deactivation_status.delete()

        # Also handle activity field updates
        elif activity_fields & update_fields:
            if hasattr(instance, "deactivation_status"):
                instance.deactivation_status.delete()


@receiver(post_save, sender=User)
def delete_sessions_of_inactive_user(sender: type[User], instance: User, **kwargs: dict) -> None:
    """Deletes the sessions of an inactive user.

    Without this, a deactivated user's sessions would start working again if the user were reactivated
    before the sessions expire.

    Args:
        sender (type[User]): The User model class.
        instance (User): The User instance being saved.
        **kwargs (dict): Additional keyword arguments from the signal.
    """
    if not instance.is_active:
        UserSession.objects.filter(user=instance).delete()
