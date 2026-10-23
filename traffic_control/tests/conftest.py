import pytest

from traffic_control.tests.factories import (
    get_api_client,
    get_user,
    OwnerFactory,
    TrafficControlDeviceTypeFactory,
)

CUSTOM_STORAGE_PATH = "traffic_control.models.common.traffic_control_device_type_icon_storage"


@pytest.fixture(autouse=True)
def settings(settings, tmp_path):
    settings.LANGUAGE_CODE = "en"
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "icons": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    return settings


@pytest.fixture
def normal_user():
    return get_user()


@pytest.fixture
def admin_api_client(admin_user):
    return get_api_client(user=admin_user)


@pytest.fixture
def user_api_client(normal_user):
    return get_api_client(user=normal_user)


@pytest.fixture
def test_owner():
    return OwnerFactory(name_fi="Helsingin kaupunki", name_en="City of Helsinki")


@pytest.fixture
def test_device_type():
    return TrafficControlDeviceTypeFactory(code="A11", description="Speed limit")


@pytest.fixture
def test_device_type_2():
    return TrafficControlDeviceTypeFactory(code="A12", description="Weight limit")
