import pytest
from django.test.utils import override_settings
from django.utils.translation import activate


@pytest.fixture(autouse=True)
def force_english():
    with override_settings(LANGUAGE_CODE="en"):
        activate("en")
        yield
