import pytest


@pytest.fixture(autouse=True)
def settings(settings):
    settings.LANGUAGE_CODE = "en"
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "icons": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    settings.TRACK_COMMAND_USAGE_APPS = ["track_example_app"]
    return settings
