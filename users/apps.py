from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "users"
    verbose_name = _("Users")

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        # https://docs.djangoproject.com/en/4.2/topics/signals/#connecting-receiver-functions
        import users.signals  # noqa: F401
