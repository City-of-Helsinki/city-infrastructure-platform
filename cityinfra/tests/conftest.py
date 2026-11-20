"""Shared fixtures for the cityinfra tests."""

import pytest
from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(autouse=True)
def plain_static_files_storage(settings: SettingsWrapper) -> SettingsWrapper:
    """Uses plain static file storage so that pages render without a static files manifest.

    Pages using `{% static %}` fail with `ManifestStaticFilesStorage` when `collectstatic` has not been run,
    which is the case in CI.

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
