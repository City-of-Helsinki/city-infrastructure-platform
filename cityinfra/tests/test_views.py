import os
from tempfile import TemporaryDirectory

import pytest
from django.core.files.storage import FileSystemStorage
from django.test import Client, override_settings
from django.urls import reverse


@pytest.fixture
def tmp_storage():
    """
    Fixture to set up a temporary directory as the default file storage
    for the duration of the test.
    """
    with TemporaryDirectory() as tmpdir:
        # Create a FileSystemStorage instance pointing to the temp directory
        temp_storages_settings = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {
                    "location": tmpdir,
                },
            }
        }
        # Override Django's default storage setting to use our temp location
        with override_settings(MEDIA_ROOT=tmpdir, STORAGES=temp_storages_settings):
            # The storage location is now tmpdir.
            # You might need to adjust settings.STORAGES if using Django 4.2+
            # For simplicity, we stick to MEDIA_ROOT/DEFAULT_FILE_STORAGE.
            yield FileSystemStorage(location=tmpdir)


@pytest.fixture
def storage_file(tmp_storage):
    """
    Fixture to create a single test file in the temporary storage.
    """
    # Define the file content and target path relative to the storage root
    content = b"This is the private file content."
    storage_path = "planfiles/testmodel/testfile.txt"

    # Write the file using the temporary storage instance
    full_path = tmp_storage.path(storage_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(content)

    return {
        "path": storage_path,
        "content": content,
        "folder": "planfiles",
        "model_name": "testmodel",
        "file_id": "testfile.txt",
    }


@pytest.mark.django_db
def test__health_check(client, settings):
    env_name = "envname"
    version = "abc123"
    settings.ENVIRONMENT_NAME = env_name
    settings.VERSION = version

    url = reverse("health-check")
    response = client.get(url)
    response_json = response.json()

    assert response.status_code == 200
    assert response_json.get("status") == "OK"
    assert response_json.get("service") == "city-infrastructure-platform"
    assert response_json.get("environment") == env_name
    assert response_json.get("version") == version


@pytest.mark.django_db
def test__file_proxy_view_good_file(client: Client, tmp_storage, storage_file):
    """
    Tests that accessing the uploaded files proxy endpoint
    """
    url = reverse(
        "planfiles_proxy",
        kwargs={
            "model_name": "testmodel",
            "file_id": "testfile.txt",
        },
    )
    expected_content = storage_file["content"]
    expected_filename = storage_file["file_id"]

    response = client.get(url)
    response_content = b"".join(response.streaming_content)

    assert response.status_code == 200
    assert response_content == expected_content
    assert response["Content-Type"] == "text/plain"
    assert response["Content-Disposition"] == f'inline; filename="{expected_filename}"'


@pytest.mark.django_db
def test__file_proxy_view_other_url_404(client: Client, tmp_storage, storage_file):
    """
    Tests that accessing a different (non-existent) path returns a 404.
    """
    url = reverse(
        "planfiles_proxy",
        kwargs={
            "model_name": "testmodel",
            "file_id": "bogus.txt",
        },
    )
    response = client.get(url)
    assert response.status_code == 404
