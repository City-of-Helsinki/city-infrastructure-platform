import importlib
import json
from http import HTTPStatus

import django.urls.resolvers
import pytest
from django.test import Client, override_settings
from django.urls import reverse

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle
from traffic_control.models import AdditionalSignPlan, AdditionalSignReal
from traffic_control.tests.factories import (
    get_additional_sign_plan,
    get_additional_sign_real,
    get_owner,
    get_traffic_control_device_type,
    get_user,
)
from traffic_control.tests.models.test_traffic_control_device_type import content_valid_by_simple_schema, simple_schema
from traffic_control.tests.test_base_api import test_point

settings_overrides = override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")


def setup_module():
    settings_overrides.enable()
    _reload_urls()


def teardown_module():
    settings_overrides.disable()
    _reload_urls()


def _reload_urls():
    urls = importlib.import_module("city-infrastructure-platform.urls")
    importlib.reload(urls)
    django.urls.resolvers._get_cached_resolver.cache_clear()


@pytest.mark.parametrize(
    ("model", "url_name"),
    (
        (AdditionalSignPlan, "additionalsignplan"),
        (AdditionalSignReal, "additionalsignreal"),
    ),
    ids=("plan", "real"),
)
@pytest.mark.django_db
def test__additional_sign__create_missing_content(client: Client, model, url_name):
    client.force_login(get_user(admin=True))
    device_type = get_traffic_control_device_type(
        content_schema=simple_schema,
        target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN,
    )

    assert model.objects.count() == 0

    data = {
        "missing_content": True,
        "content_s": "null",
        "location": test_point.ewkt,
        "owner": str(get_owner().pk),
        "device_type": str(device_type.pk),
        "z_coord": 0,
        "direction": 0,
        "order": 0,
        "lifecycle": Lifecycle.ACTIVE.value,
        "operations-TOTAL_FORMS": 0,
        "operations-INITIAL_FORMS": 0,
        "replacement_to_old-TOTAL_FORMS": 0,
        "replacement_to_old-INITIAL_FORMS": 0,
        "replacement_to_new-TOTAL_FORMS": 0,
        "replacement_to_new-INITIAL_FORMS": 0,
    }
    response = client.post(reverse(f"admin:traffic_control_{url_name}_add"), data=data)

    assert response.status_code == HTTPStatus.FOUND
    assert model.objects.count() == 1
    assert model.objects.first().missing_content is True
    assert model.objects.first().content_s is None
    assert model.objects.first().device_type == device_type


@pytest.mark.parametrize(
    ("model", "factory", "url_name"),
    (
        (AdditionalSignPlan, get_additional_sign_plan, "additionalsignplan"),
        (AdditionalSignReal, get_additional_sign_real, "additionalsignreal"),
    ),
    ids=("plan", "real"),
)
@pytest.mark.django_db
def test__additional_sign__update_device_with_content_to_missing_content(client: Client, model, factory, url_name):
    client.force_login(get_user(admin=True))
    device_type = get_traffic_control_device_type(content_schema=simple_schema)
    device = factory(device_type=device_type, content_s=content_valid_by_simple_schema)

    assert model.objects.count() == 1
    assert model.objects.get(id=device.id).missing_content is False
    assert model.objects.get(id=device.id).content_s is not None
    assert model.objects.get(id=device.id).device_type == device_type

    data = {
        "missing_content": True,
        "content_s": "null",
        "location": test_point.ewkt,
        "owner": str(get_owner().pk),
        "device_type": str(device_type.pk),
        "z_coord": 0,
        "direction": 0,
        "order": 0,
        "lifecycle": Lifecycle.ACTIVE.value,
        "operations-TOTAL_FORMS": 0,
        "operations-INITIAL_FORMS": 0,
        "replacement_to_old-TOTAL_FORMS": 0,
        "replacement_to_old-INITIAL_FORMS": 0,
        "replacement_to_new-TOTAL_FORMS": 0,
        "replacement_to_new-INITIAL_FORMS": 0,
    }
    response = client.post(
        reverse(f"admin:traffic_control_{url_name}_change", kwargs={"object_id": device.id}),
        data=data,
    )

    assert response.status_code == HTTPStatus.FOUND
    assert model.objects.count() == 1
    assert model.objects.get(id=device.id).missing_content is True
    assert model.objects.get(id=device.id).content_s is None
    assert model.objects.get(id=device.id).device_type == device_type


@pytest.mark.parametrize(
    ("model", "factory", "url_name"),
    (
        (AdditionalSignPlan, get_additional_sign_plan, "additionalsignplan"),
        (AdditionalSignReal, get_additional_sign_real, "additionalsignreal"),
    ),
    ids=("plan", "real"),
)
@pytest.mark.django_db
def test__additional_sign__update_device_with_missing_content_to_have_content(client: Client, model, factory, url_name):
    client.force_login(get_user(admin=True))
    device_type = get_traffic_control_device_type(content_schema=simple_schema)
    device = factory(device_type=device_type, missing_content=True)

    assert model.objects.count() == 1
    assert model.objects.first().missing_content is True
    assert model.objects.first().content_s is None
    assert model.objects.first().device_type == device_type

    data = {
        "missing_content": False,
        "content_s": json.dumps(content_valid_by_simple_schema),
        "location": test_point.ewkt,
        "owner": str(get_owner().pk),
        "device_type": str(device_type.pk),
        "z_coord": 0,
        "direction": 0,
        "order": 0,
        "lifecycle": Lifecycle.ACTIVE.value,
        "operations-TOTAL_FORMS": 0,
        "operations-INITIAL_FORMS": 0,
        "replacement_to_old-TOTAL_FORMS": 0,
        "replacement_to_old-INITIAL_FORMS": 0,
        "replacement_to_new-TOTAL_FORMS": 0,
        "replacement_to_new-INITIAL_FORMS": 0,
    }
    response = client.post(
        reverse(f"admin:traffic_control_{url_name}_change", kwargs={"object_id": device.id}),
        data=data,
    )

    assert response.status_code == HTTPStatus.FOUND
    assert model.objects.get(id=device.id).content_s == content_valid_by_simple_schema
    assert model.objects.get(id=device.id).missing_content is False
    assert model.objects.get(id=device.id).device_type == device_type


@pytest.mark.parametrize(
    ("model", "url_name"),
    (
        (AdditionalSignPlan, "additionalsignplan"),
        (AdditionalSignReal, "additionalsignreal"),
    ),
    ids=("plan", "real"),
)
@pytest.mark.django_db
def test__additional_sign__create_dont_accept_content_when_missing_content_is_enabled(client: Client, model, url_name):
    client.force_login(get_user(admin=True))
    device_type = get_traffic_control_device_type(content_schema=simple_schema)

    data = {
        "location": test_point.ewkt,
        "owner": str(get_owner().pk),
        "device_type": str(device_type.pk),
        "content_s": json.dumps(content_valid_by_simple_schema),
        "missing_content": True,
    }

    response = client.post(reverse(f"admin:traffic_control_{url_name}_add"), data=data)

    assert response.status_code == HTTPStatus.OK
    assert model.objects.count() == 0
    assert "missing_content" in response.context["adminform"].form.errors


@pytest.mark.parametrize(
    ("model", "factory", "url_name"),
    (
        (AdditionalSignPlan, get_additional_sign_plan, "additionalsignplan"),
        (AdditionalSignReal, get_additional_sign_real, "additionalsignreal"),
    ),
    ids=("plan", "real"),
)
@pytest.mark.django_db
def test__additional_sign__update_dont_accept_content_when_missing_content_is_enabled(
    client: Client, model, factory, url_name
):
    client.force_login(get_user(admin=True))
    device_type = get_traffic_control_device_type(content_schema=simple_schema)
    device = factory(device_type=device_type, content_s=content_valid_by_simple_schema)

    data = {
        "missing_content": True,
        "content_s": json.dumps(content_valid_by_simple_schema),
        "location": test_point.ewkt,
        "owner": str(get_owner().pk),
        "device_type": str(device_type.pk),
        "z_coord": 0,
        "direction": 0,
        "order": 0,
        "lifecycle": Lifecycle.ACTIVE.value,
        "operations-TOTAL_FORMS": 0,
        "operations-INITIAL_FORMS": 0,
    }
    response = client.post(
        reverse(f"admin:traffic_control_{url_name}_change", kwargs={"object_id": device.id}),
        data=data,
    )

    assert response.status_code == HTTPStatus.OK
    assert model.objects.count() == 1
    assert model.objects.get(id=device.id).content_s == device.content_s
    assert model.objects.get(id=device.id).missing_content is False
    assert "missing_content" in response.context["adminform"].form.errors
