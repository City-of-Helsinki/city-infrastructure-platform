from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommandTrackerConfig(AppConfig):
    name = "command_tracker"
    verbose_name = _("Management Command Usage Tracker")
