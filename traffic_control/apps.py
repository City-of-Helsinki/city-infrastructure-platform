from django.apps import AppConfig
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from traffic_control.file_registry import UPLOAD_PATH_TO_MODEL_MAP


class TrafficControlConfig(AppConfig):
    name = "traffic_control"
    verbose_name = _("Traffic control")

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        # https://docs.djangoproject.com/en/4.2/topics/signals/#connecting-receiver-functions
        # Register all AbstractFileModel-derived models onto a UPLOAD_PATH_TO_MODEL_MAP for the sake of enabling
        # FileProxyView to check for the correct view permissions before returning the file or appropriate error
        from django.apps import apps  # noqa: F401

        import traffic_control.signals  # noqa: F401
        from traffic_control.mixins.models import AbstractFileModel  # noqa: F401

        # Register audit log signals after all models are loaded
        from traffic_control.signals import register_auditlog_signals

        register_auditlog_signals()

        for model in apps.get_models():
            if not issubclass(model, AbstractFileModel) or model._meta.abstract:
                continue

            # Validate the integrity of our AbstractFileModel child classes
            try:
                file_field = model._meta.get_field("file")
            except FieldDoesNotExist:
                raise ImproperlyConfigured(
                    f"Model '{model._meta.label}' inherits from AbstractFileModel but does not define a 'file' field."
                )
            upload_to_path = getattr(file_field, "upload_to", None)
            if not upload_to_path:
                raise ImproperlyConfigured(
                    f"Model '{model._meta.label}' has a 'file' field but is missing the 'upload_to' attribute."
                )
            lookup_key = str(upload_to_path).strip("/")
            if lookup_key in UPLOAD_PATH_TO_MODEL_MAP:
                existing_model = UPLOAD_PATH_TO_MODEL_MAP[lookup_key]
                raise ImproperlyConfigured(
                    f"Duplicate upload_to path: '{lookup_key}'. Both {model._meta.label} and"
                    f"{existing_model._meta.label} use this path, which prevents finding out the appropriate model to "
                    "check permissions from when accessing FileProxyView."
                )

            UPLOAD_PATH_TO_MODEL_MAP[lookup_key] = model
