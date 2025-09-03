from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CityFurnitureConfig(AppConfig):
    name = "city_furniture"
    verbose_name = _("City furniture")

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        # https://docs.djangoproject.com/en/4.2/topics/signals/#connecting-receiver-functions
        import city_furniture.signals  # noqa: F401
