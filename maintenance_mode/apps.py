from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MaintenanceModeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "maintenance_mode"
    verbose_name = _("Maintenance Mode")
