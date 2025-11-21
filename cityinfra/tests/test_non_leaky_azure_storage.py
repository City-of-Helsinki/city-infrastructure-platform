from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains
from storages.backends.azure_storage import AzureStorage

from cityinfra.storages.backends.non_leaky_azure_storage import NonLeakyAzureStorage
from traffic_control.admin.barrier import BarrierPlanFileAdmin
from traffic_control.tests.factories import BarrierPlanFactory, BarrierPlanFileFactory

SECRET = "se=2023-01-01&sp=r&sv=2018-11-09&sr=b&sig=secret_signature"

AZURE_OPTIONS = {
    "account_name": "sas-key-user",
    "azure_container": "private-container",
    "sas_token": SECRET,
}


@pytest.mark.parametrize(
    "storage_class, expect_sas_token",
    (
        (AzureStorage, True),  # NOTE: If this case fails double-check if we still need a NonLeakyAzureStorage
        (NonLeakyAzureStorage, False),
    ),
)
def test_storage_class_url_leakage(storage_class, expect_sas_token):
    storage = storage_class(**AZURE_OPTIONS)
    file_url = storage.url("test_file.txt")
    assert ("secret_signature" in file_url) == expect_sas_token


LEAKY_STORAGE_SETTINGS_OVERRIDE = {
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": AZURE_OPTIONS,
    },
}


@pytest.mark.django_db
@override_settings(
    AZURE_ACCOUNT_NAME="sas-key-user",
    AZURE_CONTAINER="private-container",
    AZURE_SAS_TOKEN=SECRET,
    STORAGES=LEAKY_STORAGE_SETTINGS_OVERRIDE,
)
def test_regular_azure_storage_leaks_sas_token_in_list_view(admin_client):
    # We override the list display to offer the non-proxied file field as well so we risk leaking the SAS key
    with patch.object(BarrierPlanFileAdmin, "list_display", ("id", "file", "file_proxy")):
        barrier_plan = BarrierPlanFactory()
        BarrierPlanFileFactory(file="test_file.txt", barrier_plan=barrier_plan)

        list_url = reverse("admin:traffic_control_barrierplanfile_changelist")
        response = admin_client.get(list_url)

        assertContains(response, "test_file.txt")
        assertContains(response, "secret_signature")


NON_LEAKY_STORAGE_SETTINGS_OVERRIDE = {
    "default": {
        "BACKEND": "cityinfra.storages.backends.non_leaky_azure_storage.NonLeakyAzureStorage",
        "OPTIONS": AZURE_OPTIONS,
    },
}


@pytest.mark.django_db
@override_settings(
    AZURE_ACCOUNT_NAME="sas-key-user",
    AZURE_CONTAINER="private-container",
    AZURE_SAS_TOKEN=SECRET,
    STORAGES=NON_LEAKY_STORAGE_SETTINGS_OVERRIDE,
)
def test_admin_list_view_doesnt_leak_key_with_nonleaky_storage(admin_client):
    # We override the list display to offer the non-proxied file field as well so we risk leaking the SAS key
    with patch.object(BarrierPlanFileAdmin, "list_display", ("id", "file", "file_proxy")):
        barrier_plan = BarrierPlanFactory()
        BarrierPlanFileFactory(file="test_file.txt", barrier_plan=barrier_plan)

        list_url = reverse("admin:traffic_control_barrierplanfile_changelist")
        response = admin_client.get(list_url)

        assertContains(response, "test_file.txt")
        assertNotContains(response, "secret_signature")


@pytest.mark.django_db
@override_settings(
    AZURE_ACCOUNT_NAME="sas-key-user",
    AZURE_CONTAINER="private-container",
    AZURE_SAS_TOKEN=SECRET,
    STORAGES=NON_LEAKY_STORAGE_SETTINGS_OVERRIDE,
)
def test_admin_detail_view_doesnt_leak_key_with_nonleaky_storage(admin_client):
    barrier_plan = BarrierPlanFactory()
    barrier_plan_file = BarrierPlanFileFactory(file="test_file.txt", barrier_plan=barrier_plan)

    detail_url = reverse("admin:traffic_control_barrierplanfile_change", args=[barrier_plan_file.pk])
    response = admin_client.get(detail_url)

    assertContains(response, "test_file.txt")
    assertNotContains(response, "secret_signature")
