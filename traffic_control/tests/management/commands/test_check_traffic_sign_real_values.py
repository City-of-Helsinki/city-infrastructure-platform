import csv
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError

from traffic_control.analyze_utils import traffic_sign_value_check
from traffic_control.models import TrafficSignValueCheckRunInfo
from traffic_control.tests.analyze_utils.test_traffic_sign_value_check import (
    C21_FAMILY,
    create_sign,
    write_families_json,
)
from traffic_control.tests.factories import get_user
from users.utils import get_system_user


@pytest.fixture(autouse=True)
def c21_families(monkeypatch):
    """Limit the known families to the C21 example family."""
    monkeypatch.setattr(traffic_sign_value_check, "TRAFFIC_SIGN_VALUE_FAMILIES", {"C21": C21_FAMILY})


def run_command(**kwargs):
    """Run the management command and return its stdout."""
    stdout = StringIO()
    call_command("check_traffic_sign_real_values", stdout=stdout, **kwargs)
    return stdout.getvalue()


@pytest.mark.django_db
def test_command_reports_problems():
    create_sign("C21", Decimal("2.1"))
    create_sign("C21_3", Decimal("2.4"))

    output = run_command()

    assert "Traffic sign reals checked: 2" in output
    assert f"{traffic_sign_value_check.GENERIC_WITH_SUBCODE_VALUE}: 1" in output
    assert f"{traffic_sign_value_check.SUBCODE_WRONG_VALUE}: 1" in output
    assert "Found 2 traffic sign reals with a value problem." in output


@pytest.mark.django_db
def test_command_prints_expected_values():
    generic_sign = create_sign("C21", Decimal("2.1"))
    subcode_sign = create_sign("C21_3", Decimal("2.4"))

    output = run_command()

    assert "C21: 1 (generic code, expected value: any value that is not a subcode value)" in output
    assert "C21_3: 1 (expected value: 2.1)" in output
    assert "C21_3 has value 2.40, expected value: 2.1" in output
    assert "C21 has value 2.10, which is the expected value of subcode C21_3" in output
    assert str(generic_sign.id) in output
    assert str(subcode_sign.id) in output


@pytest.mark.django_db
def test_command_limits_printed_details():
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C21_3", Decimal("2.5"))

    output = run_command(max_details=1)

    assert "(Showing first 1 of 2 problems." in output
    assert output.count("Link to edit:") == 1


@pytest.mark.django_db
def test_command_prints_all_details_with_zero_limit():
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C21_3", Decimal("2.5"))

    output = run_command(max_details=0)

    assert "Showing first" not in output
    assert output.count("Link to edit:") == 2


@pytest.mark.django_db
def test_command_without_problems():
    create_sign("C21_3", Decimal("2.1"))

    output = run_command()

    assert "No value problems found." in output


@pytest.mark.django_db
def test_command_writes_csv_report(tmp_path):
    sign = create_sign("C21_3", Decimal("2.4"))
    csv_path = tmp_path / "report.csv"

    output = run_command(output_csv=str(csv_path))

    with open(csv_path, encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert f"Wrote 1 rows to {csv_path}" in output
    assert len(rows) == 1
    assert rows[0]["id"] == str(sign.id)


@pytest.mark.django_db
def test_command_does_not_write_csv_without_problems(tmp_path):
    create_sign("C21_3", Decimal("2.1"))
    csv_path = tmp_path / "report.csv"

    run_command(output_csv=str(csv_path))

    assert not csv_path.exists()


@pytest.mark.django_db
def test_command_warns_about_missing_device_types():
    create_sign("C21_3", Decimal("2.1"))

    output = run_command()

    assert "No device type found for code(s): C21, C21_2" in output


@pytest.mark.django_db
def test_command_includes_inactive_signs_when_requested():
    sign = create_sign("C21_3", Decimal("2.4"))
    sign.soft_delete(get_user())

    assert "No value problems found." in run_command()
    assert "Found 1 traffic sign reals with a value problem." in run_command(include_inactive=True)


@pytest.mark.django_db
def test_command_with_unknown_code_raises():
    with pytest.raises(CommandError):
        run_command(codes=["C99"])


@pytest.mark.django_db
def test_command_checks_extra_families_from_json(tmp_path):
    create_sign("D10_2", Decimal("50"))
    path = write_families_json(tmp_path, '{"D10": {"default_value": "50", "subcodes": {"D10_2": "60"}}}')

    output = run_command(extra_families=path, codes=["D10"])

    assert "Traffic sign reals checked: 1" in output
    assert "D10_2: 1 (expected value: 60)" in output
    assert "Found 1 traffic sign reals with a value problem." in output


@pytest.mark.django_db
def test_command_extra_families_override_built_in_family(tmp_path):
    create_sign("C21_3", Decimal("2.1"))
    path = write_families_json(tmp_path, '{"C21": {"default_value": "2.2", "subcodes": {"C21_3": "9.9"}}}')

    output = run_command(extra_families=path)

    assert "C21_3: 1 (expected value: 9.9)" in output


@pytest.mark.django_db
def test_command_with_invalid_extra_families_file_raises(tmp_path):
    path = write_families_json(tmp_path, "{ not json")

    with pytest.raises(CommandError, match="is not valid JSON"):
        run_command(extra_families=path)


@pytest.mark.django_db
def test_command_with_missing_extra_families_file_raises(tmp_path):
    with pytest.raises(CommandError, match="Could not read extra families file"):
        run_command(extra_families=str(tmp_path / "missing.json"))


@pytest.mark.django_db
def test_command_without_fix_does_not_change_anything():
    sign = create_sign("C21_3", Decimal("2.4"))

    output = run_command()
    sign.refresh_from_db()

    assert sign.value == Decimal("2.4")
    assert "Applied Fixes" not in output


@pytest.mark.django_db
def test_command_fix_applies_the_fixes():
    sign = create_sign("C21_3", None)

    output = run_command(fix=True)
    sign.refresh_from_db()

    assert sign.value == Decimal("2.1")
    assert "=== Applied Fixes ===" in output
    assert f"{traffic_sign_value_check.SUBCODE_MISSING_VALUE}: 1" in output
    assert "C21_3 value no value -> 2.1" in output
    assert "1 traffic sign reals fixed." in output


@pytest.mark.django_db
def test_command_fix_stamps_updated_by_with_system_user():
    sign = create_sign("C21_3", None)

    run_command(fix=True)
    sign.refresh_from_db()

    assert sign.updated_by == get_system_user()


@pytest.mark.django_db
def test_command_dry_run_reports_fixes_without_writing():
    sign = create_sign("C21_3", None)

    output = run_command(dry_run=True)
    sign.refresh_from_db()

    assert sign.value is None
    assert "=== Fixes That Would Be Made ===" in output
    assert "C21_3 value no value -> 2.1" in output
    assert "1 traffic sign reals would be fixed." in output


@pytest.mark.django_db
def test_command_dry_run_wins_over_fix():
    sign = create_sign("C21_3", None)

    output = run_command(fix=True, dry_run=True)
    sign.refresh_from_db()

    assert sign.value is None
    assert "=== Fixes That Would Be Made ===" in output


@pytest.mark.django_db
def test_command_fix_reports_skipped_fixes():
    sign = create_sign("C21", Decimal("2.1"))

    output = run_command(fix=True)
    sign.refresh_from_db()

    assert sign.value == Decimal("2.1")
    assert "Skipped fixes (1):" in output
    assert "C21 -> C21_3: device type 'C21_3' does not exist" in output
    assert "0 traffic sign reals fixed." in output


@pytest.mark.django_db
def test_command_fix_respects_max_details():
    create_sign("C21_3", None)
    create_sign("C21_4", None)

    output = run_command(fix=True, max_details=1)

    assert "(and 1 more, use --max-details 0 to see all)" in output
    assert "2 traffic sign reals fixed." in output


@pytest.mark.django_db
def test_command_csv_report_records_the_applied_fixes(tmp_path):
    create_sign("C21_3", None)
    csv_path = tmp_path / "report.csv"

    run_command(fix=True, output_csv=str(csv_path))

    with open(csv_path, encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_FIXED
    assert rows[0]["fix"] == "C21_3 value no value -> 2.1"


@pytest.mark.django_db
def test_command_csv_report_records_dry_run_fixes(tmp_path):
    create_sign("C21_3", None)
    csv_path = tmp_path / "report.csv"

    run_command(dry_run=True, output_csv=str(csv_path))

    with open(csv_path, encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_WOULD_BE_FIXED


@pytest.mark.django_db
def test_run_info_is_saved_for_a_report_only_run():
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C21_4", Decimal("2.3"))

    run_command()

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is False
    assert run_info.checked_count == 2
    assert run_info.problem_count == 1
    assert run_info.fixed_count == 0
    assert run_info.skipped_fix_count == 0
    assert run_info.start_time <= run_info.end_time


@pytest.mark.django_db
def test_run_info_records_the_checked_codes():
    create_sign("C21_3", Decimal("2.4"))

    run_command()

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.checked_codes == ["C21", "C21_2", "C21_3", "C21_4", "C21_5", "C21_6"]


@pytest.mark.django_db
def test_run_info_records_the_problems():
    sign = create_sign("C21_3", Decimal("2.4"))

    run_command()

    problem = TrafficSignValueCheckRunInfo.objects.get().problems[0]
    assert problem["id"] == str(sign.id)
    assert problem["device_type_code"] == "C21_3"
    assert problem["expected_value"] == "2.1"
    assert problem["fix_status"] == traffic_sign_value_check.FIX_STATUS_NOT_REQUESTED


@pytest.mark.django_db
def test_run_info_of_a_dry_run_is_not_a_database_update():
    create_sign("C21_3", None)

    run_command(dry_run=True)

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is False
    assert run_info.fixed_count == 1
    assert run_info.problems[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_WOULD_BE_FIXED


@pytest.mark.django_db
def test_run_info_of_a_fix_run_is_a_database_update():
    create_sign("C21_3", None)

    run_command(fix=True)

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is True
    assert run_info.fixed_count == 1
    assert run_info.problems[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_FIXED


@pytest.mark.django_db
def test_run_info_of_a_fix_run_without_problems_is_not_a_database_update():
    create_sign("C21_3", Decimal("2.1"))

    run_command(fix=True)

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is False
    assert run_info.problem_count == 0
    assert run_info.problems == []


@pytest.mark.django_db
def test_run_info_records_skipped_fixes():
    create_sign("C21", Decimal("2.1"))

    run_command(fix=True)

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is False
    assert run_info.skipped_fix_count == 1
    assert run_info.fixed_count == 0
    assert run_info.problems[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_SKIPPED


@pytest.mark.django_db
def test_run_info_is_saved_for_every_run():
    create_sign("C21_3", Decimal("2.4"))

    run_command()
    run_command()

    assert TrafficSignValueCheckRunInfo.objects.count() == 2


@pytest.mark.django_db
def test_failing_to_save_the_run_info_does_not_lose_the_fixes(monkeypatch):
    sign = create_sign("C21_3", None)
    monkeypatch.setattr(
        TrafficSignValueCheckRunInfo.objects,
        "create",
        lambda **kwargs: (_ for _ in ()).throw(DatabaseError("no room")),
    )

    output = run_command(fix=True)

    sign.refresh_from_db()
    assert sign.value == Decimal("2.1")
    assert "Could not save the run info: no room" in output


@pytest.mark.django_db
def test_command_fix_skips_wrong_subcode_values():
    sign = create_sign("C21_3", Decimal("2.4"))

    output = run_command(fix=True)
    sign.refresh_from_db()

    assert sign.value == Decimal("2.4")
    assert "0 traffic sign reals fixed." in output
    assert f"C21_3: {traffic_sign_value_check.AMBIGUOUS_FIX_REASON}" in output


@pytest.mark.django_db
def test_run_info_records_wrong_subcode_values_as_skipped():
    create_sign("C21_3", Decimal("2.4"))

    run_command(fix=True)

    run_info = TrafficSignValueCheckRunInfo.objects.get()
    assert run_info.database_update is False
    assert run_info.fixed_count == 0
    assert run_info.skipped_fix_count == 1
    assert run_info.problems[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_SKIPPED
