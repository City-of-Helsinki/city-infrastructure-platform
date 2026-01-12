from django.apps import AppConfig


class MaintenanceModeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "maintenance_mode"
    verbose_name = "Maintenance Mode"
