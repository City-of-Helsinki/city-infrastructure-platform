from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SiteAlertConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "site_alert"
    verbose_name = _("Site Alerts")
