import copy
import os
import shutil
from unittest import mock

import pytest
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.test.utils import override_settings
from django.utils.translation import activate

CUSTOM_STORAGE_PATH = "traffic_control.models.common.traffic_control_device_type_icon_storage"


@pytest.fixture(scope="function")
def temp_icon_storage(tmp_path):
    """
    1. Sets up a temporary MEDIA_ROOT.
    2. Patches the custom storage to use FileSystemStorage pointing to that temp location.
    3. INJECTS a temporary 'icons' configuration into settings.STORAGES.
    4. Manually cleans up the temporary directory.
    """
    temp_media_dir = tmp_path / "test_media"
    # --- 1. Define Temporary Storage Config ---
    temp_icon_storage_config = {
        # Using a simple backend for local testing/cleanup
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            # The 'location' points to our temporary path (as a string)
            "location": str(temp_media_dir),
            "azure_container": "media",
            "connection_string": "DefaultEndpointsProtocol=http;AccountName=teststore1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10/teststore1;",
        },
    }

    # Create a mutable copy of the current STORAGES settings, handling case where it might be missing
    temp_storages = copy.deepcopy(getattr(settings, "STORAGES", {}))
    # Inject or Override the 'icons' key
    temp_storages["icons"] = temp_icon_storage_config

    # Wrap all logic inside the STORAGES override to ensure the 'icons' config is present
    with override_settings(STORAGES=temp_storages):
        # Apply the MEDIA_ROOT override for cleanup purposes
        with override_settings(MEDIA_ROOT=str(temp_media_dir)):
            # Patch the custom storage function/callable
            # This ensures the model's 'storage=' argument uses the temporary FileSystemStorage
            with mock.patch(CUSTOM_STORAGE_PATH) as mock_custom_storage:
                # Configure the mock to return a FileSystemStorage instance
                mock_custom_storage.return_value = FileSystemStorage(location=temp_media_dir)
                # The 'yield' pauses the fixture execution and runs the test
                yield str(temp_media_dir)

    # This block is outside the 'with' statements, ensuring it runs during teardown.
    if os.path.exists(temp_media_dir):
        # tmp_path should handle this, but an explicit cleanup is maintained as requested
        shutil.rmtree(temp_media_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def force_english():
    with override_settings(LANGUAGE_CODE="en"):
        activate("en")
        yield
