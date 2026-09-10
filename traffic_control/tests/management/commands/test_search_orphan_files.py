from unittest.mock import patch

import pytest
from django.core.files.storage import storages
from django.core.management import call_command

from traffic_control.models import (
    AdditionalSignPlanFile,
    SearchOrphanFilesRunInfo,
    TrafficControlDeviceTypeIcon,
)
from traffic_control.tests.factories import AdditionalSignPlanFactory


@pytest.fixture
def mock_default_files():
    """Mocks list_all() on the existing default storage instance."""
    # create=True handles test environments where the local storage doesn't natively have list_all()
    with patch.object(storages["default"], "list_all", create=True, return_value=[]) as mock:
        yield mock


@pytest.fixture
def mock_icon_files():
    """Mocks list_all() on the existing icons storage instance."""
    with patch.object(storages["icons"], "list_all", create=True, return_value=[]) as mock:
        yield mock


@pytest.fixture(autouse=True)
def force_icon_sizes(settings):
    """Use pytest-django's built-in settings fixture instead of override_settings."""
    settings.PNG_ICON_SIZES = [32, 64]


# --- Test Cases ---


@pytest.mark.django_db
def test_no_problems_detected(mock_default_files, mock_icon_files):
    """Test standard perfect match behavior where storage contents match DB references exactly."""
    mock_default_files.return_value = ["planfiles/additional_sign/file1.pdf"]
    mock_icon_files.return_value = [
        "icons/traffic_control_device_type/svg/icon.svg",
        "icons/traffic_control_device_type/png/32/icon.png",
        "icons/traffic_control_device_type/png/64/icon.png",
    ]

    plan = AdditionalSignPlanFactory()
    AdditionalSignPlanFile.objects.create(additional_sign_plan=plan, file="planfiles/additional_sign/file1.pdf")
    TrafficControlDeviceTypeIcon.objects.create(file="icons/traffic_control_device_type/svg/icon.svg")

    call_command("search_orphan_files")

    assert SearchOrphanFilesRunInfo.objects.exists()
    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    assert "planfiles/additional_sign/file1.pdf" not in log
    assert "icons/traffic_control_device_type/svg/icon.svg" not in log
    assert "icons/traffic_control_device_type/png/32/icon.png" not in log
    assert "icons/traffic_control_device_type/png/64/icon.png" not in log


@pytest.mark.django_db
def test_orphan_and_dangling_attachments(mock_default_files, mock_icon_files):
    """
    Test detection of default storage files missing DB references (orphans) and DB entries missing files (dangling).
    """
    mock_default_files.return_value = [
        "planfiles/additional_sign/orphan.pdf",
        "planfiles/additional_sign/valid.pdf",
    ]

    plan = AdditionalSignPlanFactory()
    dangling = AdditionalSignPlanFile.objects.create(
        additional_sign_plan=plan, file="planfiles/additional_sign/dangling.pdf"
    )
    AdditionalSignPlanFile.objects.create(additional_sign_plan=plan, file="planfiles/additional_sign/valid.pdf")

    call_command("search_orphan_files")

    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    # Orphan attachments
    assert "Orphan attachments" in log
    assert "planfiles/additional_sign/orphan.pdf" in log

    # Dangling attachments
    assert "Dangling attachment references" in log
    assert "planfiles/additional_sign/dangling.pdf" in log
    assert f"AdditionalSignPlanFile.file (PK: {dangling.pk})" in log

    # Valid attachments
    assert "planfiles/additional_sign/valid.pdf" not in log


@pytest.mark.django_db
def test_orphan_and_dangling_icons(mock_default_files, mock_icon_files):
    """Test detection of unreferenced SVG icons (orphan) and missing storage files for DB entries (dangling)."""
    mock_icon_files.return_value = [
        "icons/traffic_control_device_type/svg/orphan.svg",
    ]

    dangling_icon = TrafficControlDeviceTypeIcon.objects.create(
        file="icons/traffic_control_device_type/svg/dangling.svg"
    )

    call_command("search_orphan_files")

    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    assert "Orphan icons" in log
    assert "icons/traffic_control_device_type/svg/orphan.svg" in log

    assert "Dangling icon references" in log
    assert "icons/traffic_control_device_type/svg/dangling.svg" in log
    assert f"TrafficControlDeviceTypeIcon.file (PK: {dangling_icon.pk})" in log


@pytest.mark.django_db
def test_missing_and_orphan_pngs(mock_default_files, mock_icon_files):
    """Test that valid SVGs missing PNG renders are detected, and stranded PNGs missing SVGs are surfaced."""
    mock_icon_files.return_value = [
        "icons/traffic_control_device_type/svg/valid.svg",
        "icons/traffic_control_device_type/png/32/valid.png",
        # Intentionally missing the 64px render for 'valid.svg'
        "icons/traffic_control_device_type/png/32/orphan.png",  # No parent SVG exists
    ]

    TrafficControlDeviceTypeIcon.objects.create(file="icons/traffic_control_device_type/svg/valid.svg")

    call_command("search_orphan_files")

    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    assert "Missing PNGs" in log
    assert "icons/traffic_control_device_type/svg/valid.svg (missing sizes: 64)" in log

    assert "Orphan PNGs" in log
    assert (
        "icons/traffic_control_device_type/png/32/orphan.png "
        "(expected SVG: icons/traffic_control_device_type/svg/orphan.svg)"
    ) in log


@pytest.mark.django_db
def test_odd_files(mock_default_files, mock_icon_files):
    """Test that rogue files not fitting prefix rules or matching icon path layouts fall into the odd bucket."""
    mock_default_files.return_value = ["weird_folder/odd_attachment.pdf"]
    mock_icon_files.return_value = [
        "icons/garbage.txt",
        "icons/traffic_control_device_type/svg/not_svg.jpg",
    ]

    call_command("search_orphan_files")

    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    assert "Odd files" in log
    assert "weird_folder/odd_attachment.pdf" in log
    assert "icons/garbage.txt" in log
    assert "icons/traffic_control_device_type/svg/not_svg.jpg" in log
