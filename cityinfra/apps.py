from django.apps import AppConfig

from cityinfra.auditlog_patches import patch_auditlog_pii_leak


class CityInfraConfig(AppConfig):
    name = "cityinfra"

    def ready(self):
        patch_auditlog_pii_leak()
