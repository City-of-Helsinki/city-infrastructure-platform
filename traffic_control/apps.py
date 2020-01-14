from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TrafficControlConfig(AppConfig):
    name = "traffic_control"
    verbose_name = _("Traffic control")
