"""Tests for importing Furniture Signpost attachment files through the admin import."""

import shutil
import tempfile

import pytest
from django.core.files.base import ContentFile
from django.test.utils import override_settings
from django.urls import reverse
from tablib import Dataset

from city_furniture.models import FurnitureSignpostReal
from city_furniture.models.furniture_signpost import FurnitureSignpostRealFile
from city_furniture.resources.furniture_signpost import FurnitureSignpostRealResource
from city_furniture.tests.factories import FurnitureSignpostRealFactory, get_furniture_signpost_real
from traffic_control.resources.attachments import ATTACHMENT_COLUMN_NAME
from traffic_control.services.import_attachments import discard_batch, list_staged, stage_files
from traffic_control.services.virus_scan import get_clam_av_scan_url

MEDIA_ROOT = tempfile.mkdtemp()
settings_overrides = override_settings(MEDIA_ROOT=MEDIA_ROOT)

DUMMY_OK_CLAMAV_RESPONSE = {"data": {"result": [{"is_infected": False, "name": "Ok", "viruses": []}]}}


def setup_module():
    settings_overrides.enable()


def teardown_module():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
    settings_overrides.disable()


@pytest.fixture
def mock_clamav(requests_mock):
    requests_mock.post(get_clam_av_scan_url("v1"), status_code=200, json=DUMMY_OK_CLAMAV_RESPONSE)
    return requests_mock


@pytest.fixture
def staged_batch():
    batch_id = stage_files(
        [
            ContentFile(b"first file", name="first.txt"),
            ContentFile(b"second file", name="second.txt"),
        ]
    )
    yield batch_id
    discard_batch(batch_id)


def _export_dataset(signpost: FurnitureSignpostReal, attachment_value: str) -> Dataset:
    """Export a signpost and set its attachment column to the given value."""
    exported = FurnitureSignpostRealResource().export(
        queryset=FurnitureSignpostReal.objects.filter(pk=signpost.pk),
    )
    column_index = exported.headers.index(ATTACHMENT_COLUMN_NAME)

    dataset = Dataset(headers=exported.headers)
    for row in exported:
        values = list(row)
        values[column_index] = attachment_value
        dataset.append(values)
    return dataset


def _attachment_names(signpost: FurnitureSignpostReal) -> list:
    return sorted(f.file.name.rsplit("/", 1)[-1] for f in signpost.files.all())


@pytest.mark.django_db
def test__attachment_column_is_exported():
    signpost = get_furniture_signpost_real()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"data", name="exported.txt"),
    )

    dataset = FurnitureSignpostRealResource().export()

    assert ATTACHMENT_COLUMN_NAME in dataset.headers
    assert dataset.dict[0][ATTACHMENT_COLUMN_NAME].startswith("exported")


@pytest.mark.django_db
def test__import_without_attachments_is_unaffected():
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "")

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True)

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert FurnitureSignpostReal.objects.count() == 1
    assert signpost.files.count() == 0


@pytest.mark.django_db
def test__import_with_empty_attachment_column_keeps_existing_attachments():
    """An empty attachment column must never remove a device's existing attachments."""
    signpost = get_furniture_signpost_real()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"keep me", name="keep.txt"),
    )
    dataset = _export_dataset(signpost, "")

    result = FurnitureSignpostRealResource().import_data(dataset, raise_errors=True)

    assert not result.has_errors()
    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("keep")


@pytest.mark.django_db
def test__import_without_attachment_column_keeps_existing_attachments(staged_batch):
    """A data file that has no attachment column at all must leave attachments untouched."""
    signpost = get_furniture_signpost_real()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"keep me", name="keep.txt"),
    )
    dataset = _export_dataset(signpost, "")
    del dataset[ATTACHMENT_COLUMN_NAME]

    result = FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert not result.has_errors()
    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("keep")


@pytest.mark.django_db
def test__import_with_empty_attachment_column_keeps_attachments_even_when_files_uploaded(staged_batch):
    """Uploading files must not touch devices whose rows do not list any of them."""
    signpost = get_furniture_signpost_real()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"keep me", name="keep.txt"),
    )
    dataset = _export_dataset(signpost, "")

    FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("keep")


@pytest.mark.django_db
def test__import_attaches_single_file(staged_batch):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt")

    result = FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert not result.has_errors()
    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("first")


@pytest.mark.django_db
def test__import_attaches_multiple_files(staged_batch):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt;second.txt")

    result = FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert not result.has_errors()
    assert signpost.files.count() == 2
    names = _attachment_names(signpost)
    assert names[0].startswith("first")
    assert names[1].startswith("second")


@pytest.mark.django_db
def test__import_replaces_existing_attachments(staged_batch):
    signpost = get_furniture_signpost_real()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"old data", name="old.txt"),
    )
    dataset = _export_dataset(signpost, "first.txt")

    FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("first")


@pytest.mark.django_db
def test__import_missing_attachment_fails_row(staged_batch):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt;missing.txt")

    result = FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset)

    assert result.has_validation_errors()
    assert "missing.txt" in str(result.invalid_rows[0].error)
    assert signpost.files.count() == 0


@pytest.mark.django_db
def test__import_without_uploaded_files_fails_row():
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt")

    result = FurnitureSignpostRealResource().import_data(dataset)

    assert result.has_validation_errors()
    assert signpost.files.count() == 0


@pytest.mark.django_db
def test__import_dry_run_does_not_attach_files(staged_batch):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt")

    result = FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, dry_run=True)

    assert not result.has_errors()
    assert not result.has_validation_errors()
    assert signpost.files.count() == 0


@pytest.mark.django_db
def test__unchanged_row_with_attachments_is_not_skipped(staged_batch):
    """``skip_unchanged`` must not prevent attachments from being applied."""
    signpost = FurnitureSignpostRealFactory()
    dataset = _export_dataset(signpost, "first.txt")

    FurnitureSignpostRealResource(attachment_batch_id=staged_batch).import_data(dataset, raise_errors=True)

    assert signpost.files.count() == 1


@pytest.mark.django_db
def test__admin_import__attaches_files_and_discards_batch(admin_client, mock_clamav):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "first.txt")
    url = reverse("admin:city_furniture_furnituresignpostreal_import")

    import_response = admin_client.post(
        url,
        data={
            "import_file": ContentFile(dataset.csv.encode("utf-8"), name="signposts.csv"),
            "format": "0",
            "attachment_files": ContentFile(b"first file", name="first.txt"),
        },
    )

    assert import_response.status_code == 200
    confirm_form = import_response.context["confirm_form"]
    batch_id = confirm_form.initial["attachment_batch_id"]
    assert batch_id
    assert set(list_staged(batch_id)) == {"first.txt"}

    process_response = admin_client.post(
        reverse("admin:city_furniture_furnituresignpostreal_process_import"),
        data={**confirm_form.initial, "attachment_batch_id": batch_id},
    )

    assert process_response.status_code == 302
    assert signpost.files.count() == 1
    assert _attachment_names(signpost)[0].startswith("first")
    assert list_staged(batch_id) == {}


@pytest.mark.django_db
def test__admin_import__missing_attachment_shows_row_error(admin_client, mock_clamav):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "missing.txt")
    url = reverse("admin:city_furniture_furnituresignpostreal_import")

    response = admin_client.post(
        url,
        data={
            "import_file": ContentFile(dataset.csv.encode("utf-8"), name="signposts.csv"),
            "format": "0",
            "attachment_files": ContentFile(b"first file", name="first.txt"),
        },
    )

    assert response.status_code == 200
    assert "confirm_form" not in response.context
    assert response.context["result"].has_validation_errors()
    assert signpost.files.count() == 0


@pytest.mark.django_db
def test__admin_import__illegal_attachment_type_is_a_form_error(admin_client, mock_clamav):
    signpost = get_furniture_signpost_real()
    dataset = _export_dataset(signpost, "")
    url = reverse("admin:city_furniture_furnituresignpostreal_import")

    response = admin_client.post(
        url,
        data={
            "import_file": ContentFile(dataset.csv.encode("utf-8"), name="signposts.csv"),
            "format": "0",
            "attachment_files": ContentFile(b"nope", name="malicious.illegal"),
        },
    )

    assert response.status_code == 200
    assert "attachment_files" in response.context["form"].errors
