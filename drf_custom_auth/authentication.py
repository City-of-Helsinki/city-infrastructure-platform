"""Custom DRF authentication classes that update last_api_use on successful authentication."""

from typing import Optional, Tuple

from django.utils import timezone
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.request import Request

from users.models import User


def _update_last_api_use(user: User) -> None:
    """
    Update the last_api_use field for a user if not already set today.

    Skips the DB write if last_api_use is already today's date to avoid
    unnecessary writes on every request. Uses queryset.update() to avoid
    triggering the post_save signal.

    Args:
        user (User): The authenticated user to update.
    """
    today = timezone.now().date()
    if user.last_api_use != today:
        User.objects.filter(pk=user.pk).update(last_api_use=today)
        user.last_api_use = today


class LastApiUseMixin:
    """Mixin that updates last_api_use on successful DRF authentication."""

    def authenticate(self, request: Request) -> Optional[Tuple]:
        """
        Authenticate the request and update last_api_use on success.

        Args:
            request (Request): The incoming DRF request.

        Returns:
            Optional[Tuple]: Tuple of (user, auth) on success, or None if
                authentication was not attempted.
        """
        result = super().authenticate(request)
        if result is not None:
            _update_last_api_use(result[0])
        return result


class LastApiUseBasicAuthentication(LastApiUseMixin, BasicAuthentication):
    """BasicAuthentication subclass that updates last_api_use on successful authentication."""


class LastApiUseTokenAuthentication(LastApiUseMixin, TokenAuthentication):
    """TokenAuthentication subclass that updates last_api_use on successful authentication."""
