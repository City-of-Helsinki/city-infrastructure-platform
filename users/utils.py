from .models import User


def get_system_user():
    user, _ = User.objects.get_or_create(
        username="system",
        is_active=False,
        is_staff=False,
    )
    return user
