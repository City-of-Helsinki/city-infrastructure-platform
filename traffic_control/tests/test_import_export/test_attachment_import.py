"""Tests for staging and applying attachment files uploaded with an admin import."""

import shutil
import tempfile
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from import_export.formats.base_formats import CSV

from city_furniture.models.furniture_signpost import FurnitureSignpostRealFile
from city_furniture.resources.furniture_signpost import FurnitureSignpostRealResource
from city_furniture.tests.factories import FurnitureSignpostRealFactory
from traffic_control.resources.attachments import (
    AppendAttachmentsStrategy,
    AppendSkipExistingAttachmentsStrategy,
    ATTACHMENT_COLUMN_NAME,
    parse_attachment_filenames,
    ReplaceAttachmentsStrategy,
)
from traffic_control.resources.forms import AttachmentConfirmImportForm, AttachmentImportForm
from traffic_control.services.import_attachments import (
    AttachmentStagingError,
    discard_batch,
    discard_stale_batches,
    list_batch_ids,
    list_staged,
    open_staged,
    sanitize_filename,
    stage_files,
    stage_import_attachments,
)
from traffic_control.services.virus_scan import get_clam_av_scan_url

MEDIA_ROOT = tempfile.mkdtemp()
settings_overrides = override_settings(MEDIA_ROOT=MEDIA_ROOT)

DUMMY_OK_CLAMAV_RESPONSE = {"data": {"result": [{"is_infected": False, "name": "Ok", "viruses": []}]}}
DUMMY_INFECTED_CLAMAV_RESPONSE = {
    "data": {"result": [{"is_infected": True, "name": "virus.txt", "viruses": ["Eicar-Test-Signature"]}]}
}


def setup_module():
    settings_overrides.enable()


def teardown_module():
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
    settings_overrides.disable()


@pytest.fixture
def mock_clamav(requests_mock):
    requests_mock.post(get_clam_av_scan_url("v1"), status_code=200, json=DUMMY_OK_CLAMAV_RESPONSE)
    return requests_mock


def _content_file(name: str, content: bytes = b"content") -> ContentFile:
    return ContentFile(content, name=name)


# Staging service


def test__stage_files__round_trip():
    batch_id = stage_files([_content_file("first.txt", b"one"), _content_file("second.pdf", b"two")])

    try:
        staged = list_staged(batch_id)
        assert set(staged) == {"first.txt", "second.pdf"}
        with open_staged(batch_id, "first.txt") as staged_file:
            assert staged_file.read() == b"one"
    finally:
        discard_batch(batch_id)

    assert list_staged(batch_id) == {}


def test__stage_files__no_files_returns_none():
    assert stage_files([]) is None


def test__stage_files__duplicate_names_rejected():
    with pytest.raises(AttachmentStagingError):
        stage_files([_content_file("same.txt"), _content_file("same.txt")])


def test__stage_files__strips_directories_from_names():
    batch_id = stage_files([_content_file("some/dir/nested.txt")])

    try:
        assert set(list_staged(batch_id)) == {"nested.txt"}
    finally:
        discard_batch(batch_id)


@pytest.mark.parametrize("filename", ["", "   ", "..", "/"])
def test__sanitize_filename__invalid(filename):
    with pytest.raises(AttachmentStagingError):
        sanitize_filename(filename)


def test__open_staged__unknown_file():
    batch_id = stage_files([_content_file("known.txt")])

    try:
        with pytest.raises(AttachmentStagingError):
            open_staged(batch_id, "unknown.txt")
    finally:
        discard_batch(batch_id)


def test__list_staged__unknown_batch_is_empty():
    assert list_staged("90a1ff9a-6f24-4e1e-9c02-0e3a3f5a5f52") == {}


def test__list_staged__invalid_batch_id():
    with pytest.raises(AttachmentStagingError):
        list_staged("not-a-uuid")


def test__discard_stale_batches__keeps_fresh_batches():
    batch_id = stage_files([_content_file("fresh.txt")])

    try:
        assert batch_id not in discard_stale_batches(timedelta(hours=1))
        assert set(list_staged(batch_id)) == {"fresh.txt"}
        assert batch_id in discard_stale_batches(timedelta(seconds=0))
        assert list_staged(batch_id) == {}
    finally:
        discard_batch(batch_id)


# Column parsing


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, []),
        ("", []),
        ("a.txt", ["a.txt"]),
        ("a.txt;b.txt", ["a.txt", "b.txt"]),
        (" a.txt ; b.txt ", ["a.txt", "b.txt"]),
        ("a.txt;a.txt", ["a.txt"]),
        ("a.txt;;b.txt", ["a.txt", "b.txt"]),
    ],
)
def test__parse_attachment_filenames(value, expected):
    assert parse_attachment_filenames(value) == expected


# Upload validation


def test__stage_import_attachments__illegal_file_type(mock_clamav):
    with pytest.raises(ValidationError, match="Illegal file types"):
        stage_import_attachments([_content_file("malicious.illegal")])


def test__stage_import_attachments__virus_found(requests_mock):
    requests_mock.post(get_clam_av_scan_url("v1"), status_code=200, json=DUMMY_INFECTED_CLAMAV_RESPONSE)

    with pytest.raises(ValidationError, match="Virus scan failure"):
        stage_import_attachments([_content_file("virus.txt")])


def test__stage_import_attachments__no_files(mock_clamav):
    assert stage_import_attachments([]) is None


def test__stage_import_attachments__success(mock_clamav):
    batch_id = stage_import_attachments([_content_file("ok.txt")])

    try:
        assert set(list_staged(batch_id)) == {"ok.txt"}
    finally:
        discard_batch(batch_id)


# Strategies


@pytest.mark.django_db
def test__replace_attachments_strategy():
    signpost = FurnitureSignpostRealFactory()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"old", name="old.txt"),
    )
    batch_id = stage_files([_content_file("new.txt")])

    try:
        ReplaceAttachmentsStrategy().apply(
            signpost, FurnitureSignpostRealFile, "furniture_signpost_real", ["new.txt"], batch_id
        )
    finally:
        discard_batch(batch_id)

    filenames = [f.file.name.rsplit("/", 1)[-1] for f in signpost.files.all()]
    assert len(filenames) == 1
    assert filenames[0].startswith("new")


@pytest.mark.django_db
def test__append_attachments_strategy():
    signpost = FurnitureSignpostRealFactory()
    FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"old", name="old.txt"),
    )
    batch_id = stage_files([_content_file("new.txt")])

    try:
        AppendAttachmentsStrategy().apply(
            signpost, FurnitureSignpostRealFile, "furniture_signpost_real", ["new.txt"], batch_id
        )
    finally:
        discard_batch(batch_id)

    assert signpost.files.count() == 2


@pytest.mark.django_db
def test__append_skip_existing_attachments_strategy():
    signpost = FurnitureSignpostRealFactory()
    existing = FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"old", name="same.txt"),
    )
    existing_name = existing.file.name.rsplit("/", 1)[-1]
    batch_id = stage_files([_content_file(existing_name), _content_file("other.txt")])

    try:
        AppendSkipExistingAttachmentsStrategy().apply(
            signpost,
            FurnitureSignpostRealFile,
            "furniture_signpost_real",
            [existing_name, "other.txt"],
            batch_id,
        )
    finally:
        discard_batch(batch_id)

    assert signpost.files.count() == 2
    assert ATTACHMENT_COLUMN_NAME == "attachment_filenames"


# Selected / staged file listing in the admin UI


def test__multiple_file_input__renders_file_list_container():
    form = AttachmentImportForm(formats=[CSV], resources=[FurnitureSignpostRealResource])
    rendered = str(form["attachment_files"])

    assert "data-attachment-file-list" in rendered
    assert 'data-input-id="id_attachment_files"' in rendered
    assert "No files selected" in rendered
    assert "Selected files" in rendered
    assert "traffic_control/js/import_attachment_files.js" in str(form.media)


def test__confirm_form__lists_staged_attachment_names():
    batch_id = stage_files([_content_file("second.txt"), _content_file("first.txt")])

    try:
        form = AttachmentConfirmImportForm(initial={"attachment_batch_id": batch_id})
        assert form.staged_attachment_names == ["first.txt", "second.txt"]
    finally:
        discard_batch(batch_id)


def test__confirm_form__without_batch_has_no_staged_names():
    assert AttachmentConfirmImportForm(initial={}).staged_attachment_names == []


def test__confirm_form__invalid_batch_id_is_ignored():
    assert AttachmentConfirmImportForm(initial={"attachment_batch_id": "not-a-uuid"}).staged_attachment_names == []


# Storage backend prefix semantics


class _AzureLikeStorage(FileSystemStorage):
    """Storage whose ``listdir`` mimics ``AzureStorage``'s plain prefix semantics.

    ``AzureStorage`` strips the given path as a plain prefix from the blob names, so listing
    ``dir`` instead of ``dir/`` reports every blob as a directory named ``""`` and returns no
    files at all.
    """

    def listdir(self, path=""):
        directories, filenames = super().listdir(path.rstrip("/"))
        if path and not path.endswith("/"):
            return [""], []
        return directories, filenames


def test__list_staged__works_with_azure_prefix_semantics(monkeypatch):
    storage = _AzureLikeStorage(location=MEDIA_ROOT)
    monkeypatch.setattr("traffic_control.services.import_attachments.get_staging_storage", lambda: storage)

    batch_id = stage_files([_content_file("first.txt"), _content_file("second.pdf")])

    try:
        assert set(list_staged(batch_id)) == {"first.txt", "second.pdf"}
        assert batch_id in list_batch_ids()
    finally:
        discard_batch(batch_id)

    assert list_staged(batch_id) == {}


# Already attached files referenced by the attachment column


def _attach(signpost, filename: str) -> str:
    """Attach a file to a signpost and return its stored base name."""
    attachment = FurnitureSignpostRealFile.objects.create(
        furniture_signpost_real=signpost,
        file=ContentFile(b"content", name=filename),
    )
    return attachment.file.name.rsplit("/", 1)[-1]


@pytest.mark.django_db
def test__replace_strategy__keeps_listed_existing_and_deletes_unlisted():
    """Re-importing an export with one name removed keeps the other file without re-uploading."""
    signpost = FurnitureSignpostRealFactory()
    kept = _attach(signpost, "Test1.txt")
    removed = _attach(signpost, "test2.txt")

    ReplaceAttachmentsStrategy().apply(
        signpost, FurnitureSignpostRealFile, "furniture_signpost_real", [kept], batch_id=None
    )

    remaining = [f.file.name.rsplit("/", 1)[-1] for f in signpost.files.all()]
    assert remaining == [kept]
    assert removed not in remaining


@pytest.mark.django_db
def test__replace_strategy__keeps_existing_and_adds_newly_staged():
    signpost = FurnitureSignpostRealFactory()
    kept = _attach(signpost, "Test1.txt")
    batch_id = stage_files([_content_file("third.txt")])

    try:
        ReplaceAttachmentsStrategy().apply(
            signpost,
            FurnitureSignpostRealFile,
            "furniture_signpost_real",
            [kept, "third.txt"],
            batch_id,
        )
    finally:
        discard_batch(batch_id)

    remaining = sorted(f.file.name.rsplit("/", 1)[-1] for f in signpost.files.all())
    assert kept in remaining
    assert any(name.startswith("third") for name in remaining)
    assert len(remaining) == 2


@pytest.mark.django_db
def test__before_import_row__accepts_already_attached_file():
    signpost = FurnitureSignpostRealFactory()
    attached = _attach(signpost, "Test1.txt")
    resource = FurnitureSignpostRealResource(attachment_batch_id=None)

    resource.before_import_row({"id": str(signpost.pk), ATTACHMENT_COLUMN_NAME: attached})


@pytest.mark.django_db
def test__before_import_row__rejects_unknown_file():
    signpost = FurnitureSignpostRealFactory()
    resource = FurnitureSignpostRealResource(attachment_batch_id=None)

    with pytest.raises(ValidationError) as error:
        resource.before_import_row({"id": str(signpost.pk), ATTACHMENT_COLUMN_NAME: "nope.txt"})

    assert "nope.txt" in str(error.value)


@pytest.mark.django_db
def test__before_import_row__new_row_still_requires_upload():
    resource = FurnitureSignpostRealResource(attachment_batch_id=None)

    with pytest.raises(ValidationError):
        resource.before_import_row({"id": "", ATTACHMENT_COLUMN_NAME: "Test1.txt"})
