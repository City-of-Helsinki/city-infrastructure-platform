"""Signal handlers for the users app."""

from typing import Optional

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from users.models import User


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
