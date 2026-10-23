import pytest


@pytest.fixture(autouse=True)
def settings(settings):
    settings.LANGUAGE_CODE = "en"
    return settings
