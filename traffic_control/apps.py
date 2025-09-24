from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TrafficControlConfig(AppConfig):
    name = "traffic_control"
    verbose_name = _("Traffic control")

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        # https://docs.djangoproject.com/en/4.2/topics/signals/#connecting-receiver-functions
        import traffic_control.signals  # noqa: F401
