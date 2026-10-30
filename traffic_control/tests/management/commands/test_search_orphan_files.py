import pytest
from django.core.files.storage import storages
from django.core.management import call_command

from traffic_control.models import (
    AdditionalSignPlanFile,
    SearchOrphanFilesRunInfo,
    TrafficControlDeviceTypeIcon,
)
from traffic_control.tests.factories import AdditionalSignPlanFactory


@pytest.fixture(autouse=True)
def settings(settings):
    """Use pytest-django's built-in settings fixture instead of override_settings."""
    settings.PNG_ICON_SIZES = [32, 64]


# The tests below override the storage's list_all method, which does not exist in
# django.core.files.storage.FileSystemStorage, but is treated by the command as if
# it exists


@pytest.mark.django_db
def test_no_problems_detected(monkeypatch):
    """Test standard perfect match behavior where storage contents match DB references exactly."""

    def default_files():
        return ["planfiles/additional_sign/file1.pdf"]

    def icon_files():
        return [
            "icons/traffic_control_device_type/svg/icon.svg",
            "icons/traffic_control_device_type/png/32/icon.png",
            "icons/traffic_control_device_type/png/64/icon.png",
        ]

    monkeypatch.setattr(storages["default"], "list_all", default_files, raising=False)
    monkeypatch.setattr(storages["icons"], "list_all", icon_files, raising=False)

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
def test_orphan_and_dangling_attachments(monkeypatch):
    """
    Test detection of default storage files missing DB references (orphans) and DB entries missing files (dangling).
    """

    def default_files():
        return ["planfiles/additional_sign/orphan.pdf", "planfiles/additional_sign/valid.pdf"]

    monkeypatch.setattr(storages["default"], "list_all", default_files, raising=False)

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
def test_orphan_and_dangling_icons(monkeypatch):
    """Test detection of unreferenced SVG icons (orphan) and missing storage files for DB entries (dangling)."""

    def icon_files():
        return ["icons/traffic_control_device_type/svg/orphan.svg"]

    monkeypatch.setattr(storages["icons"], "list_all", icon_files, raising=False)

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
def test_missing_and_orphan_pngs(monkeypatch):
    """Test that valid SVGs missing PNG renders are detected, and stranded PNGs missing SVGs are surfaced."""

    def icon_files():
        return [
            "icons/traffic_control_device_type/svg/valid.svg",
            "icons/traffic_control_device_type/png/32/valid.png",
            "icons/traffic_control_device_type/png/32/orphan.png",
        ]

    monkeypatch.setattr(storages["icons"], "list_all", icon_files, raising=False)

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
def test_odd_files(monkeypatch):
    """Test that rogue files not fitting prefix rules or matching icon path layouts fall into the odd bucket."""

    def default_files():
        return ["weird_folder/odd_attachment.pdf"]

    def icon_files():
        return ["icons/garbage.txt", "icons/traffic_control_device_type/svg/not_svg.jpg"]

    monkeypatch.setattr(storages["default"], "list_all", default_files, raising=False)
    monkeypatch.setattr(storages["icons"], "list_all", icon_files, raising=False)

    call_command("search_orphan_files")

    run_info = SearchOrphanFilesRunInfo.objects.last()
    log = run_info.execution_log

    assert "Odd files" in log
    assert "weird_folder/odd_attachment.pdf" in log
    assert "icons/garbage.txt" in log
    assert "icons/traffic_control_device_type/svg/not_svg.jpg" in log
