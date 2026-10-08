"""Tests for staging and applying attachment files uploaded with an admin import."""

import shutil
import tempfile
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test.utils import override_settings

from city_furniture.models.furniture_signpost import FurnitureSignpostRealFile
from city_furniture.tests.factories import FurnitureSignpostRealFactory
from traffic_control.resources.attachments import (
    AppendAttachmentsStrategy,
    AppendSkipExistingAttachmentsStrategy,
    ATTACHMENT_COLUMN_NAME,
    parse_attachment_filenames,
    ReplaceAttachmentsStrategy,
)
from traffic_control.services.import_attachments import (
    AttachmentStagingError,
    discard_batch,
    discard_stale_batches,
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
