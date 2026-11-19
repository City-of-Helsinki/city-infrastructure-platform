import pytest
from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(autouse=True)
def settings(settings: SettingsWrapper) -> SettingsWrapper:
    """Use plain static file storage so the maintenance page renders without a static files manifest.

    The maintenance page uses `{% static %}`, which fails with `ManifestStaticFilesStorage` when no manifest exists.

    Args:
        settings (SettingsWrapper): The pytest-django settings fixture.

    Returns:
        SettingsWrapper: The modified settings fixture.
    """
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "icons": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    return settings
