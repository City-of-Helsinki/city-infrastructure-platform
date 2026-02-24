from .models import User


def get_system_user():
    user, _ = User.objects.get_or_create(
        username="system",
        is_active=False,
        is_staff=False,
    )
    return user


def get_admin_notification_recipients() -> list[str]:
    """
    Get list of email addresses for users who receive admin notifications.

    Returns:
        list[str]: List of email addresses for admin notification recipients.
                  Returns empty list if no admins are configured.
    """
    admin_users = User.objects.filter(
        receives_admin_notification_emails=True, email__isnull=False, is_active=True
    ).exclude(email="")

    return list(admin_users.values_list("email", flat=True))
