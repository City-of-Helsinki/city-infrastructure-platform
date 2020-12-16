from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MapConfig(AppConfig):
    name = "map"
    verbose_name = _("Map")
