from django.test import override_settings

settings_overrides = override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "icons": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    TRACK_COMMAND_USAGE_APPS=["track_example_app"],
)


def setup_module():
    settings_overrides.enable()


def teardown_module():
    settings_overrides.disable()
