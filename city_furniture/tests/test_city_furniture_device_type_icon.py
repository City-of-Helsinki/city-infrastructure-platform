import os
from tempfile import TemporaryDirectory

import pytest
from auditlog.models import LogEntry
from django.db import IntegrityError

from city_furniture.models.common import CityFurnitureDeviceTypeIcon
from city_furniture.tests.factories import CityFurnitureDeviceTypeIconFactory


@pytest.fixture
def override_settings(settings):
    """Override MEDIA_ROOT for tests to avoid cluttering the project's media folder."""
    settings.MEDIA_ROOT = TemporaryDirectory().name


@pytest.mark.xfail(reason="Requires azurite storage or django >=5.1+, django 4.2 simply renames the file")
@pytest.mark.django_db
def test__city_furniture_device_type_icon__enforces_uniqueness(override_settings):
    """
    We don't want two separate rows meaning the same file in our table.
    This test ensures the database uniqueness constraint on the 'file' field is active.
    """
    # The factory's `django_get_or_create` would prevent an error, so we must
    # bypass it to test the actual database constraint.
    icon1 = CityFurnitureDeviceTypeIconFactory()
    with pytest.raises(IntegrityError):
        # Attempt to create a new record with the exact same file path
        CityFurnitureDeviceTypeIcon.objects.create(file=icon1.file)


@pytest.mark.django_db
def test__city_furniture_device_type_icon__custom_signal_handlers(override_settings, settings):
    """
    Check that creating and deleting CityFurnitureDeviceTypeIcon objects correctly
    triggers the side effect of creating and deleting corresponding PNG icon files.
    """
    td = CityFurnitureDeviceTypeIconFactory()
    storage = td.file.storage
    svg_name = os.path.basename(td.file.name)
    png_name = svg_name.replace(".svg", ".png")

    # Check that after object creation the files are in the right place
    assert storage.exists(os.path.join(settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION, svg_name))
    for size in settings.PNG_ICON_SIZES:
        assert storage.exists(
            os.path.join(
                settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION,
                str(size),
                png_name,
            )
        )

    # Check that after object deletion the files have been wiped
    td.delete()
    assert not storage.exists(os.path.join(settings.CITY_FURNITURE_DEVICE_TYPE_SVG_ICON_DESTINATION, svg_name))
    for size in settings.PNG_ICON_SIZES:
        assert not storage.exists(
            os.path.join(
                settings.CITY_FURNITURE_DEVICE_TYPE_PNG_ICON_DESTINATION,
                str(size),
                png_name,
            )
        )


@pytest.mark.django_db
def test__city_furniture_device_type_icon__auditlog_entries(override_settings):
    """
    Test that create, change, and delete actions are correctly recorded in the audit log.
    """
    # 1. Test CREATE action
    icon = CityFurnitureDeviceTypeIconFactory()
    logs = LogEntry.objects.get_for_object(icon)
    assert logs.count() == 1
    create_log = logs.first()
    assert create_log.action == LogEntry.Action.CREATE
    assert create_log.content_type.get_object_for_this_type(pk=create_log.object_pk) == icon

    # 2. Test CHANGE (update) action
    # Use the factory's .build() strategy to generate a new file object
    # without creating another database record.
    new_file_data = CityFurnitureDeviceTypeIconFactory.build()
    icon.file = new_file_data.file
    icon.save()

    logs = LogEntry.objects.get_for_object(icon)
    assert logs.count() == 2
    update_log = logs.latest("timestamp")
    assert update_log.action == LogEntry.Action.UPDATE
    assert update_log.content_type.get_object_for_this_type(pk=update_log.object_pk) == icon
    assert "file" in update_log.changes_dict

    # 3. Test DELETE action
    icon_pk = icon.pk
    icon_str = str(icon)
    icon.delete()

    # After deletion, query by model and PK since the object is gone
    logs = LogEntry.objects.get_for_model(CityFurnitureDeviceTypeIcon).filter(object_pk=str(icon_pk))
    assert logs.count() == 3
    delete_log = logs.latest("timestamp")
    assert delete_log.action == LogEntry.Action.DELETE
    assert delete_log.object_pk == str(icon_pk)
    assert delete_log.object_repr == icon_str
