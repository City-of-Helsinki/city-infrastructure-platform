# traffic_control/tests/test_signal_utils.py

import pytest
from auditlog.models import LogEntry
from django.core.files.uploadedfile import SimpleUploadedFile

from traffic_control.models import AdditionalSignRealFile
from traffic_control.tests.factories import AdditionalSignRealFactory, TrafficSignRealFactory

# NOTE:
# These tests exercise the generic parent relation audit logging signals
# using real, migrated models instead of ad-hoc dynamic test models. This
# avoids interfering with Django's test database setup.
#
# Signals are registered in model modules at import time. We assume the
# project settings ensure models are imported during test collection.
# If a signal registration changes, update expectations accordingly.


@pytest.mark.django_db
def test_additional_sign_real_file_creation_logs_parent_relation():
    parent = AdditionalSignRealFactory()
    # Clear possible previous relation logs from object creation
    LogEntry.objects.filter(object_pk=str(parent.pk)).delete()

    test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
    AdditionalSignRealFile.objects.create(file=test_file, additional_sign_real=parent)

    # Fetch latest log entry for the parent
    le = (
        LogEntry.objects.filter(object_pk=str(parent.pk), content_type__model=parent._meta.model_name)
        .order_by("-id")
        .first()
    )
    assert le, "Expected a log entry for parent on file creation"
    assert le.action == LogEntry.Action.UPDATE
    relations = le.changes_dict.get("relations")
    assert relations and relations[0] is None and "was added" in relations[1]
    assert str(parent.pk) == le.object_pk


@pytest.mark.django_db
def test_additional_sign_real_file_move_logs_old_and_new_parents():
    old_parent = AdditionalSignRealFactory()
    new_parent = AdditionalSignRealFactory()
    LogEntry.objects.filter(object_pk__in=[str(old_parent.pk), str(new_parent.pk)]).delete()

    test_file = SimpleUploadedFile("move.txt", b"abc", content_type="text/plain")
    file_obj = AdditionalSignRealFile.objects.create(file=test_file, additional_sign_real=old_parent)
    # Clear creation relation log for isolation
    LogEntry.objects.filter(object_pk=str(old_parent.pk)).delete()

    file_obj.additional_sign_real = new_parent
    file_obj.save()

    old_log = (
        LogEntry.objects.filter(object_pk=str(old_parent.pk), content_type__model=old_parent._meta.model_name)
        .order_by("-id")
        .first()
    )
    new_log = (
        LogEntry.objects.filter(object_pk=str(new_parent.pk), content_type__model=new_parent._meta.model_name)
        .order_by("-id")
        .first()
    )

    assert old_log and new_log, "Expected logs for both old and new parents"

    old_rel = old_log.changes_dict.get("relations")
    new_rel = new_log.changes_dict.get("relations")

    assert old_rel[1] is None and "was removed" in old_rel[0]
    assert new_rel[0] is None and "was added" in new_rel[1]


@pytest.mark.django_db
def test_additional_sign_real_parent_change_logs_on_traffic_sign_real():
    tsr_old = TrafficSignRealFactory()
    tsr_new = TrafficSignRealFactory()
    asr = AdditionalSignRealFactory(parent=tsr_old)

    # Remove initial addition relation log
    LogEntry.objects.filter(object_pk__in=[str(tsr_old.pk), str(tsr_new.pk)]).delete()

    asr.parent = tsr_new
    asr.save()

    old_log = (
        LogEntry.objects.filter(object_pk=str(tsr_old.pk), content_type__model=tsr_old._meta.model_name)
        .order_by("-id")
        .first()
    )
    new_log = (
        LogEntry.objects.filter(object_pk=str(tsr_new.pk), content_type__model=tsr_new._meta.model_name)
        .order_by("-id")
        .first()
    )

    assert old_log and new_log, "Expected logs for both old and new traffic sign reals"

    old_rel = old_log.changes_dict.get("relations")
    new_rel = new_log.changes_dict.get("relations")

    assert old_rel[1] is None and "was removed" in old_rel[0]
    assert new_rel[0] is None and "was added" in new_rel[1]


@pytest.mark.django_db
def test_additional_sign_real_update_without_parent_change_logs_update_on_parent():
    parent = TrafficSignRealFactory()
    asr = AdditionalSignRealFactory(parent=parent)
    LogEntry.objects.filter(object_pk=str(parent.pk)).delete()  # clear initial addition log

    # Change a field on AdditionalSignReal that does not alter parent relation
    asr.additional_information = "Updated info"
    asr.save()

    log = (
        LogEntry.objects.filter(object_pk=str(parent.pk), content_type__model=parent._meta.model_name)
        .order_by("-id")
        .first()
    )
    assert log, "Expected an update log entry on parent after child update"
    rel = log.changes_dict.get("relations")
    assert rel and rel[0] == rel[1] and "was updated" in rel[0]
