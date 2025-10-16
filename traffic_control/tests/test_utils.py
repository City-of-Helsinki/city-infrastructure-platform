from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from traffic_control.tests.factories import TrafficControlDeviceTypeIconFactory
from traffic_control.tests.utils import DummyRequestForAxes
from traffic_control.utils import get_client_ip, get_icon_upload_obstacles


@pytest.mark.parametrize(
    "address,expected,in_header",
    (
        ("1.12.123.1", "1.12.123.1", True),
        ("1.12.123.1:80", "1.12.123.1", True),
        ("1.12.123.1", "1.12.123.1", False),
        ("[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:80", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
        ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", False),
    ),
)
def test_client_ip(address, expected, in_header):
    meta = {"REMOTE_ADDR": address} if not in_header else {}
    headers = {"x-forwarded-for": address} if in_header else {}
    dummy_request = DummyRequestForAxes(meta=meta, headers=headers)
    assert get_client_ip(dummy_request) == expected


@pytest.fixture
def setup_existing_icons():
    """Fixture to create pre-existing icons for tests."""
    TrafficControlDeviceTypeIconFactory(file="icons/existing_icon.svg")
    TrafficControlDeviceTypeIconFactory(file="another_existing_icon.svg")


@pytest.mark.django_db
@override_settings(ALLOWED_FILE_UPLOAD_TYPES=[".svg"], CLAM_AV_ENABLED=True)
@pytest.mark.parametrize(
    "uploaded_files, clam_av_return_value, expected_illegal_types, expected_virus_errors, expected_existing_icons",
    [
        (
            # Case 1: Detects existing files among new ones
            [
                SimpleUploadedFile("new_icon.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
                SimpleUploadedFile("existing_icon.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
                SimpleUploadedFile("another_existing_icon.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
            ],
            {"errors": []},
            set(),
            [],
            ["another_existing_icon.svg", "existing_icon.svg"],
        ),
        (
            # Case 2: All types of errors are reported
            [
                SimpleUploadedFile("existing_icon.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
                SimpleUploadedFile("invalid_file.png", b"...", content_type="image/png"),
            ],
            {"errors": ["VIRUS"]},
            {".png"},
            ["VIRUS"],
            ["existing_icon.svg"],
        ),
        (
            # Case 3: No obstacles for valid, new files
            [
                SimpleUploadedFile("new_icon_1.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
                SimpleUploadedFile("new_icon_2.svg", b"<svg>...</svg>", content_type="image/svg+xml"),
            ],
            {"errors": []},
            set(),
            [],
            [],
        ),
    ],
)
def test_get_icon_upload_obstacles(
    setup_existing_icons,
    uploaded_files,
    clam_av_return_value,
    expected_illegal_types,
    expected_virus_errors,
    expected_existing_icons,
):
    """
    Verify that get_icon_upload_obstacles correctly identifies all upload obstacles.
    - Illegal file types
    - Virus scan errors
    - Files that already exist in the database
    """
    with patch("traffic_control.utils.clam_av_scan", return_value=clam_av_return_value) as mock_clam_av_scan:
        illegal_types, virus_scan_errors, existing_icons = get_icon_upload_obstacles(uploaded_files)

        assert illegal_types == expected_illegal_types
        assert virus_scan_errors == expected_virus_errors
        assert sorted(existing_icons) == sorted(expected_existing_icons)
        mock_clam_av_scan.assert_called_once()
