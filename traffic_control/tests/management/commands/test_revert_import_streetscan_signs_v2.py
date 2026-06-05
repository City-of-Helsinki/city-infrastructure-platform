import json
from datetime import datetime, timezone

import pytest
from django.core.management import call_command

from traffic_control.models import (
    AdditionalSignReal,
    MountReal,
    SignpostReal,
    TrafficSignReal,
)
from traffic_control.tests.factories import (
    AdditionalSignRealFactory,
    MountRealFactory,
    SignpostRealFactory,
    TrafficSignRealFactory,
    UserFactory,
)

# Test Constants
UUID_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
UUID_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
UUID_3 = "cccccccc-cccc-cccc-cccc-cccccccccccc"
UUID_4 = "dddddddd-dddd-dddd-dddd-dddddddddddd"
UUID_5 = "00000000-0000-0000-0000-000000000000"
UUID_6 = "11111111-1111-1111-1111-111111111111"
UUID_7 = "22222222-2222-2222-2222-222222222222"
UUID_8 = "33333333-3333-3333-3333-333333333333"


# --- Fixtures ---


@pytest.fixture
def base_time_created():
    return datetime(2021, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def base_time_updated():
    return datetime(2022, 2, 2, tzinfo=timezone.utc)


@pytest.fixture
def user():
    return UserFactory(
        email="erkki.esimerkki@example.com",
        first_name="Erkki",
        last_name="Esimerkki",
        username="erkki_esimerkki",
    )


def write_jsonl(tmp_path, rows: list[dict]) -> str:
    """Helper to write a list of dicts to a JSONL file and return the file path."""
    file_path = tmp_path / "revert.jsonl"
    with open(file_path, "wt") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return file_path


# --- Test Cases ---


@pytest.mark.django_db
def test_no_objects_affected_in_db(tmp_path, capsys, user, base_time_created, base_time_updated):
    """Objects exist in DB, but no objects exist that match the revert file."""
    mount = MountRealFactory(id=UUID_1, created_by=user, updated_by=user)
    signpost = SignpostRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_4, created_by=user, updated_by=user, condition=1)

    MountReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    SignpostReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_4).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "MountReal", "db_id": UUID_5, "old": {"mount_type_id": UUID_1}},
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_6, "old": {"condition": 5}},
            {"action": "deactivate", "object_type": "TrafficSignReal", "db_id": UUID_7, "old": {"condition": 5}},
            {"action": "create", "object_type": "AdditionalSignReal", "db_id": UUID_8},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path)

    additional_sign.refresh_from_db()
    mount.refresh_from_db()
    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert additional_sign.condition == 1
    assert signpost.condition == 1
    assert traffic_sign.condition == 1

    assert additional_sign.updated_at == base_time_updated
    assert mount.updated_at == base_time_updated
    assert signpost.updated_at == base_time_updated
    assert traffic_sign.updated_at == base_time_updated

    captured = capsys.readouterr()
    assert (
        "AdditionalSignReal 33333333-3333-3333-3333-333333333333 does not exist, unable to revert create operation"
        in captured.out
    )
    assert (
        "SignpostReal 11111111-1111-1111-1111-111111111111 does not exist, unable to revert update operation"
        in captured.out
    )
    assert (
        "TrafficSignReal 22222222-2222-2222-2222-222222222222 does not exist, unable to revert deactivate operation"
        in captured.out
    )
    assert (
        "MountReal 00000000-0000-0000-0000-000000000000 does not exist, unable to revert update operation"
        in captured.out
    )


@pytest.mark.django_db
def test_objects_exist_none_affected_due_to_cli_filter(tmp_path, user, base_time_created, base_time_updated):
    """Objects exist and match the file, but CLI arguments filter them out entirely."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path, ids=[UUID_4])

    additional_sign.refresh_from_db()
    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert additional_sign.condition == 1
    assert signpost.condition == 1
    assert traffic_sign.condition == 1

    assert additional_sign.updated_at == base_time_updated
    assert signpost.updated_at == base_time_updated
    assert traffic_sign.updated_at == base_time_updated


@pytest.mark.django_db
def test_objects_exist_partially_affected_due_to_id_filter(tmp_path, user, base_time_created, base_time_updated):
    """Objects exist, but only some are affected due to CLI ID filter."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path, ids=[UUID_1, UUID_3])

    additional_sign.refresh_from_db()
    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert additional_sign.condition == 5
    assert additional_sign.updated_at > base_time_updated

    assert signpost.condition == 5
    assert signpost.updated_at > base_time_updated

    assert traffic_sign.condition == 1
    assert traffic_sign.updated_at == base_time_updated


@pytest.mark.django_db
def test_objects_exist_partially_affected_due_to_model_filter(tmp_path, user, base_time_created, base_time_updated):
    """Objects exist, but only some are affected due to CLI model filter."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command(
        "revert_import_streetscan_signs_v2", file_path=file_path, models=["AdditionalSignReal", "TrafficSignReal"]
    )

    additional_sign.refresh_from_db()
    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert additional_sign.condition == 5
    assert additional_sign.updated_at > base_time_updated

    assert traffic_sign.condition == 5
    assert traffic_sign.updated_at > base_time_updated

    assert signpost.condition == 1
    assert signpost.updated_at == base_time_updated


@pytest.mark.django_db
def test_objects_exist_partially_affected_due_to_both_filters(tmp_path, user, base_time_created, base_time_updated):
    """Objects exist, but only some are affected due to CLI model and ID filters."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command(
        "revert_import_streetscan_signs_v2",
        file_path=file_path,
        models=["AdditionalSignReal", "TrafficSignReal"],
        ids=[UUID_1, UUID_3],
    )

    additional_sign.refresh_from_db()
    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert additional_sign.condition == 5
    assert additional_sign.updated_at > base_time_updated
    assert traffic_sign.condition == 1
    assert signpost.condition == 1


@pytest.mark.django_db
def test_objects_affected_no_orphans(tmp_path, capsys, user, base_time_created, base_time_updated):
    """Standard revert affecting objects without producing dependents/orphans."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path)

    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()
    additional_sign.refresh_from_db()

    assert signpost.condition == 5
    assert traffic_sign.condition == 5
    assert additional_sign.condition == 5

    captured = capsys.readouterr()
    assert "No secondary AdditionalSignReal objects orphaned" in captured.out
    assert "No secondary SignpostReal objects orphaned" in captured.out
    assert "No secondary TrafficSignReal objects orphaned" in captured.out


@pytest.mark.django_db
def test_orphans_produced_and_included_in_revert_file(tmp_path, capsys, user, base_time_created, base_time_updated):
    """Reverting a mount and a signpost creation leaves dependent signs orphaned, and their subsequent update records
    are bypassed by the initial CLI model filter but successfully processed by Phase B."""
    mount = MountRealFactory(id=UUID_1, created_by=user, updated_by=user)
    signpost = SignpostRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1, mount_real=mount)
    traffic_sign = TrafficSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1, mount_real=mount)
    additional_sign = AdditionalSignRealFactory(
        id=UUID_4, created_by=user, updated_by=user, condition=1, signpost_real=signpost
    )

    MountReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    SignpostReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_4).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "create", "object_type": "MountReal", "db_id": UUID_1},
            {"action": "create", "object_type": "SignpostReal", "db_id": UUID_2},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_3, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_4, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path, models=["MountReal", "SignpostReal"])

    assert not MountReal.objects.filter(id=UUID_1).exists()
    assert not SignpostReal.objects.filter(id=UUID_2).exists()

    traffic_sign.refresh_from_db()
    additional_sign.refresh_from_db()

    assert traffic_sign.mount_real is None
    assert traffic_sign.condition == 5

    assert additional_sign.signpost_real is None
    assert additional_sign.condition == 5

    captured = capsys.readouterr()
    assert "1 secondary TrafficSignReal objects orphaned" in captured.out
    assert "1 secondary AdditionalSignReal objects orphaned" in captured.out


@pytest.mark.django_db
def test_orphans_produced_and_excluded_by_cli_filter(tmp_path, capsys, user, base_time_created, base_time_updated):
    """Reverting creation files leaves child records orphaned; the child updates are bypassed by the CLI id filters,
    but processed completely by Phase B fallback."""
    mount = MountRealFactory(id=UUID_1, created_by=user, updated_by=user)
    signpost = SignpostRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1, mount_real=mount)
    traffic_sign = TrafficSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1, mount_real=mount)

    MountReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    SignpostReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "create", "object_type": "MountReal", "db_id": UUID_1},
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path, ids=[UUID_1])

    assert not MountReal.objects.filter(id=UUID_1).exists()

    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert signpost.mount_real is None
    assert signpost.condition == 5

    assert traffic_sign.mount_real is None
    assert traffic_sign.condition == 5

    captured = capsys.readouterr()
    assert "1 secondary SignpostReal objects orphaned" in captured.out
    assert "1 secondary TrafficSignReal objects orphaned" in captured.out


@pytest.mark.django_db
def test_orphans_produced_and_never_mentioned_in_revert_file(
    tmp_path, capsys, user, base_time_created, base_time_updated
):
    """Reverting a container leaves child components orphaned, but because they have no update data in the log, their
    attributes remain un-reverted, and a specific fallback missing update string is emitted to standard output."""
    mount = MountRealFactory(id=UUID_1, created_by=user, updated_by=user)
    signpost = SignpostRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1, mount_real=mount)
    traffic_sign = TrafficSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1, mount_real=mount)

    MountReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    SignpostReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(tmp_path, [{"action": "create", "object_type": "MountReal", "db_id": UUID_1}])

    call_command("revert_import_streetscan_signs_v2", file_path=file_path)

    assert not MountReal.objects.filter(id=UUID_1).exists()

    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()

    assert signpost.mount_real is None
    assert signpost.condition == 1

    assert traffic_sign.mount_real is None
    assert traffic_sign.condition == 1

    captured = capsys.readouterr()
    # Validate the fallback TODO implementation log structure
    assert (
        "1 secondary SignpostReal objects orphaned by reverted CREATE operations do not have pending UPDATE "
        f"operations and cannot be reverted: {UUID_2}"
    ) in captured.out
    assert (
        "1 secondary TrafficSignReal objects orphaned by reverted CREATE operations do not have pending UPDATE "
        f"operations and cannot be reverted: {UUID_3}"
    ) in captured.out


@pytest.mark.django_db
def test_dry_run(tmp_path, user, base_time_created, base_time_updated):
    """A dry run handles operations fully but transactions are rolled back leaving objects unchanged."""
    signpost = SignpostRealFactory(id=UUID_1, created_by=user, updated_by=user, condition=1)
    traffic_sign = TrafficSignRealFactory(id=UUID_2, created_by=user, updated_by=user, condition=1)
    additional_sign = AdditionalSignRealFactory(id=UUID_3, created_by=user, updated_by=user, condition=1)

    SignpostReal.objects.filter(id=UUID_1).update(updated_at=base_time_updated, created_at=base_time_created)
    TrafficSignReal.objects.filter(id=UUID_2).update(updated_at=base_time_updated, created_at=base_time_created)
    AdditionalSignReal.objects.filter(id=UUID_3).update(updated_at=base_time_updated, created_at=base_time_created)

    file_path = write_jsonl(
        tmp_path,
        [
            {"action": "update", "object_type": "SignpostReal", "db_id": UUID_1, "old": {"condition": 5}},
            {"action": "update", "object_type": "TrafficSignReal", "db_id": UUID_2, "old": {"condition": 5}},
            {"action": "update", "object_type": "AdditionalSignReal", "db_id": UUID_3, "old": {"condition": 5}},
        ],
    )

    call_command("revert_import_streetscan_signs_v2", file_path=file_path, dry_run=True)

    signpost.refresh_from_db()
    traffic_sign.refresh_from_db()
    additional_sign.refresh_from_db()

    assert signpost.condition == 1
    assert traffic_sign.condition == 1
    assert additional_sign.condition == 1
    assert signpost.updated_at == base_time_updated
    assert traffic_sign.updated_at == base_time_updated
    assert additional_sign.updated_at == base_time_updated
