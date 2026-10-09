import csv
import io
from typing import List, Tuple

import pytest
from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.db.models import Model
from django.urls import reverse

from traffic_control.models import SignpostReal
from traffic_control.resources.common import CustomImportExportActionModelAdmin
from traffic_control.resources.signpost import SignpostRealResource
from traffic_control.tests.factories import get_user, SignpostRealFactory

CSV_CONTENT_TYPE = "text/csv"


def _get_import_export_admins() -> List[Tuple[Model, CustomImportExportActionModelAdmin]]:
    """
    Collects every registered admin that provides the "Export template" link.

    Returns:
        List[Tuple[Model, CustomImportExportActionModelAdmin]]: Model and model admin pairs
            for all admins inheriting from ``CustomImportExportActionModelAdmin``.
    """
    return [
        (model, model_admin)
        for model, model_admin in admin.site._registry.items()
        if isinstance(model_admin, CustomImportExportActionModelAdmin)
    ]


IMPORT_EXPORT_ADMINS = _get_import_export_admins()
IMPORT_EXPORT_ADMIN_IDS = [model._meta.label_lower for model, _ in IMPORT_EXPORT_ADMINS]


def _get_export_empty_url(model: Model) -> str:
    """
    Builds the admin URL of the empty export template view for the given model.

    Args:
        model (Model): Model whose admin URL is resolved.

    Returns:
        str: Absolute admin path of the ``export_empty`` view.
    """
    return reverse(admin_urlname(model._meta, "export_empty"))


def _parse_csv_rows(response) -> List[List[str]]:
    """
    Parses the CSV body of an export response into rows.

    Args:
        response: Django test client response containing CSV content.

    Returns:
        List[List[str]]: Non-empty CSV rows of the response body.
    """
    content = response.content.decode("utf-8-sig")
    return [row for row in csv.reader(io.StringIO(content)) if row]


def test__export_empty_template__admins_are_found():
    assert IMPORT_EXPORT_ADMINS, "No CustomImportExportActionModelAdmin registered, parametrization would be empty"
    assert SignpostReal in dict(IMPORT_EXPORT_ADMINS)


@pytest.mark.django_db
@pytest.mark.parametrize(("model", "model_admin"), IMPORT_EXPORT_ADMINS, ids=IMPORT_EXPORT_ADMIN_IDS)
def test__export_empty_template__returns_csv_template(admin_client, model, model_admin):
    response = admin_client.get(_get_export_empty_url(model))

    assert response.status_code == 200
    assert response["Content-Type"] == CSV_CONTENT_TYPE
    assert response["Content-Disposition"] == f'attachment; filename="{model.__name__}-Template.csv"'

    rows = _parse_csv_rows(response)
    assert len(rows) == 1, "Template must contain only the header row"
    assert rows[0], "Template header row must not be empty"


@pytest.mark.django_db
def test__export_empty_template__header_matches_resource_fields(admin_client):
    response = admin_client.get(_get_export_empty_url(SignpostReal))

    rows = _parse_csv_rows(response)
    expected_columns = [field.column_name for field in SignpostRealResource().get_export_fields()]
    assert rows[0] == expected_columns


@pytest.mark.django_db
def test__export_empty_template__is_empty_even_when_objects_exist(admin_client):
    SignpostRealFactory()
    SignpostRealFactory()

    response = admin_client.get(_get_export_empty_url(SignpostReal))

    rows = _parse_csv_rows(response)
    assert len(rows) == 1, "Template must not contain any data rows"


@pytest.mark.django_db
def test__export_empty_template__anonymous_user_is_redirected_to_login(client):
    url = _get_export_empty_url(SignpostReal)

    response = client.get(url)

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


@pytest.mark.django_db
def test__export_empty_template__user_without_export_permission_is_denied(client):
    user = get_user(admin=False)
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    client.force_login(user)

    response = client.get(_get_export_empty_url(SignpostReal))

    assert response.status_code == 403
