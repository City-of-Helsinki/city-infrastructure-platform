import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest

from traffic_control.analyze_utils import traffic_sign_value_check
from traffic_control.analyze_utils.traffic_sign_value_check import TrafficSignValueChecker
from traffic_control.constants import SignValueFamily
from traffic_control.enums import Lifecycle
from traffic_control.tests.factories import get_user, TrafficControlDeviceTypeFactory, TrafficSignRealFactory
from users.utils import get_system_user

C21_FAMILY = SignValueFamily(
    generic_code="C21",
    default_value=Decimal("2.2"),
    subcodes={
        "C21_2": Decimal("2.0"),
        "C21_3": Decimal("2.1"),
        "C21_4": Decimal("2.3"),
        "C21_5": Decimal("2.4"),
        "C21_6": Decimal("2.5"),
    },
)
C22_FAMILY = SignValueFamily(
    generic_code="C22",
    default_value=Decimal("3.0"),
    subcodes={"C22_2": Decimal("2.0")},
)


@pytest.fixture(autouse=True)
def c21_families(monkeypatch):
    """Limit the known families to the C21 example family."""
    monkeypatch.setattr(traffic_sign_value_check, "TRAFFIC_SIGN_VALUE_FAMILIES", {"C21": C21_FAMILY})


def create_sign(code, value, lifecycle=Lifecycle.ACTIVE):
    """Create a traffic sign real with the given device type code, value and lifecycle."""
    device_type = TrafficControlDeviceTypeFactory(code=code, value="")
    return TrafficSignRealFactory(device_type=device_type, value=value, lifecycle=lifecycle)


def write_families_json(tmp_path, json_text):
    """Write the given JSON text into an extra families file and return its path."""
    json_path = tmp_path / "families.json"
    json_path.write_text(json_text, encoding="utf-8")
    return str(json_path)


def get_results(**kwargs):
    """Run the checker and return the found problems."""
    checker = TrafficSignValueChecker(**kwargs)
    return checker.check_signs()


def test_checked_codes_contains_generic_code_and_subcodes():
    checker = TrafficSignValueChecker()

    assert sorted(checker.checked_codes) == ["C21", "C21_2", "C21_3", "C21_4", "C21_5", "C21_6"]
    assert checker.subcode_lookup["C21_3"] == (C21_FAMILY, Decimal("2.1"))


def test_unknown_code_raises_value_error():
    with pytest.raises(ValueError):
        TrafficSignValueChecker(codes=["C99"])


@pytest.mark.django_db
def test_generic_sign_with_subcode_value_is_reported():
    sign = create_sign("C21", Decimal("2.1"))

    results = get_results()

    assert len(results) == 1
    assert results[0].sign_id == sign.id
    assert results[0].error_category == traffic_sign_value_check.GENERIC_WITH_SUBCODE_VALUE
    assert results[0].matching_subcode == "C21_3"
    assert results[0].generic_code == "C21"


@pytest.mark.django_db
@pytest.mark.parametrize("value", [Decimal("2.2"), Decimal("7.5"), None], ids=["default", "unrelated", "empty"])
def test_generic_sign_with_allowed_value_is_not_reported(value):
    create_sign("C21", value)

    assert get_results() == []


@pytest.mark.django_db
@pytest.mark.parametrize("value", [Decimal("2.1"), Decimal("2.10")], ids=["exact", "trailing_zero"])
def test_subcode_sign_with_expected_value_is_not_reported(value):
    create_sign("C21_3", value)

    assert get_results() == []


@pytest.mark.django_db
def test_subcode_sign_with_wrong_value_is_reported():
    sign = create_sign("C21_3", Decimal("2.4"))

    results = get_results()

    assert len(results) == 1
    assert results[0].sign_id == sign.id
    assert results[0].error_category == traffic_sign_value_check.SUBCODE_WRONG_VALUE
    assert results[0].expected_value == Decimal("2.1")
    assert results[0].value == Decimal("2.4")


@pytest.mark.django_db
def test_subcode_sign_with_missing_value_is_reported():
    sign = create_sign("C21_4", None)

    results = get_results()

    assert len(results) == 1
    assert results[0].sign_id == sign.id
    assert results[0].error_category == traffic_sign_value_check.SUBCODE_MISSING_VALUE
    assert results[0].expected_value == Decimal("2.3")


@pytest.mark.django_db
def test_signs_outside_families_are_ignored():
    create_sign("A11", Decimal("2.1"))

    checker = TrafficSignValueChecker()

    assert checker.check_signs() == []
    assert checker.checked_count == 0


@pytest.mark.django_db
def test_codes_argument_limits_checked_families(monkeypatch):
    monkeypatch.setattr(
        traffic_sign_value_check,
        "TRAFFIC_SIGN_VALUE_FAMILIES",
        {"C21": C21_FAMILY, "C22": C22_FAMILY},
    )
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C22_2", Decimal("2.4"))

    results = get_results(codes=["C22"])

    assert len(results) == 1
    assert results[0].device_type_code == "C22_2"


@pytest.mark.django_db
def test_soft_deleted_signs_are_excluded_by_default():
    sign = create_sign("C21_3", Decimal("2.4"))
    sign.soft_delete(get_user())

    assert get_results() == []
    assert len(get_results(include_inactive=True)) == 1


@pytest.mark.parametrize("lifecycle", [Lifecycle.TEMPORARILY_INACTIVE, Lifecycle.INACTIVE])
@pytest.mark.django_db
def test_signs_that_are_not_in_use_are_excluded_by_default(lifecycle):
    create_sign("C21_3", Decimal("2.4"), lifecycle=lifecycle)

    assert get_results() == []
    assert len(get_results(include_inactive=True)) == 1


@pytest.mark.parametrize("lifecycle", [Lifecycle.ACTIVE, Lifecycle.TEMPORARILY_ACTIVE])
@pytest.mark.django_db
def test_signs_that_are_in_use_are_checked(lifecycle):
    create_sign("C21_3", Decimal("2.4"), lifecycle=lifecycle)

    assert len(get_results()) == 1


@pytest.mark.django_db
def test_signs_that_are_not_in_use_are_not_fixed():
    sign = create_sign("C21_4", None, lifecycle=Lifecycle.INACTIVE)

    apply_fixes()
    sign.refresh_from_db()
    assert sign.value is None

    apply_fixes(include_inactive=True)
    sign.refresh_from_db()
    assert sign.value == Decimal("2.3")


@pytest.mark.django_db
def test_get_missing_device_type_codes():
    create_sign("C21_3", Decimal("2.1"))

    assert TrafficSignValueChecker().get_missing_device_type_codes() == [
        "C21",
        "C21_2",
        "C21_4",
        "C21_5",
        "C21_6",
    ]


@pytest.mark.django_db
def test_get_summary():
    create_sign("C21", Decimal("2.1"))
    create_sign("C21_3", Decimal("2.4"))

    checker = TrafficSignValueChecker()
    checker.check_signs()

    assert checker.checked_count == 2
    assert checker.get_summary() == {
        "error_category": {
            traffic_sign_value_check.GENERIC_WITH_SUBCODE_VALUE: 1,
            traffic_sign_value_check.SUBCODE_WRONG_VALUE: 1,
        },
        "generic_code": {"C21": 2},
        "device_type_code": {"C21": 1, "C21_3": 1},
    }


@pytest.mark.django_db
def test_get_code_summary():
    create_sign("C21", Decimal("2.1"))
    create_sign("C21_3", Decimal("2.4"))

    checker = TrafficSignValueChecker()
    checker.check_signs()

    assert checker.get_code_summary() == {
        "C21": {"count": 1, "expected_value": None, "is_generic": True},
        "C21_3": {"count": 1, "expected_value": Decimal("2.1"), "is_generic": False},
    }


def test_get_expected_value():
    checker = TrafficSignValueChecker()

    assert checker.get_expected_value("C21_3") == Decimal("2.1")
    assert checker.get_expected_value("C21") is None
    assert checker.get_expected_value("A11") is None


@pytest.mark.django_db
def test_result_description_contains_expected_value():
    create_sign("C21", Decimal("2.1"))
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C21_4", None)

    descriptions = sorted(result.description for result in get_results())

    assert descriptions == [
        "C21 has value 2.10, which is the expected value of subcode C21_3. Expected: any value that is "
        "not a subcode value, or device type C21_3",
        "C21_3 has value 2.40, expected value: 2.1",
        "C21_4 has no value, expected value: 2.3",
    ]


@pytest.mark.django_db
def test_write_csv_report(tmp_path):
    sign = create_sign("C21_3", Decimal("2.4"))
    csv_path = tmp_path / "report.csv"

    checker = TrafficSignValueChecker()
    checker.check_signs()
    checker.write_csv_report(str(csv_path))

    with open(csv_path, encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["id"] == str(sign.id)
    assert rows[0]["device_type_code"] == "C21_3"
    assert rows[0]["generic_code"] == "C21"
    assert rows[0]["value"] == "2.40"
    assert rows[0]["expected_value"] == "2.1"
    assert rows[0]["matching_subcode"] == ""
    assert rows[0]["error_category"] == traffic_sign_value_check.SUBCODE_WRONG_VALUE
    assert str(sign.id) in rows[0]["admin_url"]


def test_load_families_from_json(tmp_path):
    path = write_families_json(
        tmp_path,
        """
        {
          "D10": {
            "default_value": "50",
            "subcodes": {"D10_2": "60", "D10_3": 70}
          }
        }
        """,
    )

    families = traffic_sign_value_check.load_families_from_json(path)

    assert families == {
        "D10": SignValueFamily(
            generic_code="D10",
            default_value=Decimal("50"),
            subcodes={"D10_2": Decimal("60"), "D10_3": Decimal("70")},
        )
    }


def test_load_families_from_json_uses_defaults_for_omitted_keys(tmp_path):
    path = write_families_json(tmp_path, '{"362": {}, "3611": {"default_value": null}}')

    families = traffic_sign_value_check.load_families_from_json(path)

    assert families["362"] == SignValueFamily(generic_code="362", default_value=None, subcodes={})
    assert families["3611"] == SignValueFamily(generic_code="3611", default_value=None, subcodes={})


@pytest.mark.parametrize(
    "json_text,expected_message",
    [
        ('["not", "an", "object"]', "must contain a JSON object of families"),
        ("{ not json", "is not valid JSON"),
        ('{"X1": "nope"}', "Family 'X1' must be an object"),
        ('{"X1": {"subcodes": []}}', "Family 'X1': 'subcodes' must be an object"),
        ('{"X1": {"subcodes": {"X1_2": "abc"}}}', "value of subcode 'X1_2' must be a number"),
        ('{"X1": {"default_value": true}}', "Family 'X1': 'default_value' must be a number"),
    ],
)
def test_load_families_from_json_invalid_content(tmp_path, json_text, expected_message):
    path = write_families_json(tmp_path, json_text)

    with pytest.raises(ValueError, match=expected_message):
        traffic_sign_value_check.load_families_from_json(path)


def test_load_families_from_json_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Could not read extra families file"):
        traffic_sign_value_check.load_families_from_json(str(tmp_path / "missing.json"))


@pytest.mark.django_db
def test_extra_families_are_checked():
    create_sign("D10_2", Decimal("50"))
    extra_families = {
        "D10": SignValueFamily(
            generic_code="D10",
            default_value=Decimal("50"),
            subcodes={"D10_2": Decimal("60")},
        )
    }

    checker = TrafficSignValueChecker(extra_families=extra_families)
    results = checker.check_signs()

    assert sorted(checker.checked_codes) == ["C21", "C21_2", "C21_3", "C21_4", "C21_5", "C21_6", "D10", "D10_2"]
    assert len(results) == 1
    assert results[0].device_type_code == "D10_2"
    assert results[0].expected_value == Decimal("60")
    assert results[0].error_category == traffic_sign_value_check.SUBCODE_WRONG_VALUE


@pytest.mark.django_db
def test_extra_families_override_built_in_family():
    create_sign("C21_4", Decimal("2.3"))
    extra_families = {
        "C21": SignValueFamily(
            generic_code="C21",
            default_value=Decimal("2.2"),
            subcodes={"C21_4": Decimal("9.9")},
        )
    }

    checker = TrafficSignValueChecker(extra_families=extra_families)
    results = checker.check_signs()

    assert sorted(checker.checked_codes) == ["C21", "C21_4"]
    assert [(result.device_type_code, result.expected_value) for result in results] == [("C21_4", Decimal("9.9"))]


@pytest.mark.django_db
def test_extra_families_can_be_selected_with_codes():
    checker = TrafficSignValueChecker(
        codes=["D10"],
        extra_families={"D10": SignValueFamily(generic_code="D10", default_value=None, subcodes={})},
    )

    assert checker.checked_codes == ["D10"]


def get_fixes(**kwargs):
    """Run the checker and return the fixes it plans for the found problems."""
    checker = TrafficSignValueChecker(**kwargs)
    checker.check_signs()
    return checker.plan_fixes()


def apply_fixes(dry_run=False, user=None, **kwargs):
    """Run the checker and apply the fixes it plans for the found problems."""
    checker = TrafficSignValueChecker(**kwargs)
    checker.check_signs()
    return checker.apply_fixes(user=user or get_system_user(), dry_run=dry_run)


@pytest.mark.django_db
def test_wrong_subcode_value_is_not_fixed():
    """Either the value or the device type could be the wrong one, so neither is touched."""
    sign = create_sign("C21_3", Decimal("2.4"))

    fixes = apply_fixes()
    sign.refresh_from_db()

    assert sign.value == Decimal("2.4")
    assert [fix.is_skipped for fix in fixes] == [True]
    assert fixes[0].description == f"C21_3: {traffic_sign_value_check.AMBIGUOUS_FIX_REASON}"


@pytest.mark.django_db
def test_wrong_subcode_value_keeps_its_device_type():
    sign = create_sign("C21_3", Decimal("2.4"))
    original_device_type_id = sign.device_type_id

    apply_fixes()
    sign.refresh_from_db()

    assert sign.device_type_id == original_device_type_id


@pytest.mark.django_db
def test_fix_sets_expected_value_for_missing_subcode_value():
    sign = create_sign("C21_4", None)

    fixes = apply_fixes()
    sign.refresh_from_db()

    assert sign.value == Decimal("2.3")
    assert fixes[0].description == "C21_4 value no value -> 2.3"


@pytest.mark.django_db
def test_fix_moves_generic_sign_to_matching_subcode():
    sign = create_sign("C21", Decimal("2.1"))
    subcode_device_type = TrafficControlDeviceTypeFactory(code="C21_3", value="")

    fixes = apply_fixes()
    sign.refresh_from_db()

    assert sign.device_type_id == subcode_device_type.id
    assert sign.value == Decimal("2.1")
    assert fixes[0].description == "C21 -> C21_3 (value 2.10 kept)"


@pytest.mark.django_db
def test_fix_is_skipped_when_subcode_device_type_does_not_exist():
    sign = create_sign("C21", Decimal("2.1"))
    original_device_type_id = sign.device_type_id

    fixes = apply_fixes()
    sign.refresh_from_db()

    assert sign.device_type_id == original_device_type_id
    assert sign.value == Decimal("2.1")
    assert [fix.is_skipped for fix in fixes] == [True]
    assert fixes[0].description == "C21 -> C21_3: device type 'C21_3' does not exist"


@pytest.mark.django_db
def test_fix_applies_other_fixes_when_one_is_skipped():
    generic_sign = create_sign("C21", Decimal("2.1"))
    subcode_sign = create_sign("C21_4", None)

    fixes = apply_fixes()
    generic_sign.refresh_from_db()
    subcode_sign.refresh_from_db()

    assert sorted(fix.is_skipped for fix in fixes) == [False, True]
    assert generic_sign.value == Decimal("2.1")
    assert subcode_sign.value == Decimal("2.3")


@pytest.mark.django_db
def test_dry_run_does_not_write_anything():
    sign = create_sign("C21_3", None)

    fixes = apply_fixes(dry_run=True)
    sign.refresh_from_db()

    assert sign.value is None
    assert [fix.is_skipped for fix in fixes] == [False]
    assert fixes[0].target_value == Decimal("2.1")


@pytest.mark.django_db
def test_fix_stamps_updated_by_with_the_given_user():
    sign = create_sign("C21_3", None)
    previous_updated_at = sign.updated_at
    user = get_user("value-fixer")

    apply_fixes(user=user)
    sign.refresh_from_db()

    assert sign.updated_by == user
    assert sign.updated_at > previous_updated_at


@pytest.mark.django_db
def test_fixed_signs_have_no_problems_on_a_re_run():
    create_sign("C21_3", None)
    create_sign("C21_4", None)

    apply_fixes()

    assert get_results() == []


@pytest.mark.django_db
def test_fixes_are_limited_to_the_selected_codes():
    c21_sign = create_sign("C21_3", None)
    d10_sign = create_sign("D10_2", None)
    extra_families = {"D10": SignValueFamily(generic_code="D10", default_value=None, subcodes={"D10_2": Decimal("60")})}

    apply_fixes(codes=["D10"], extra_families=extra_families)
    c21_sign.refresh_from_db()
    d10_sign.refresh_from_db()

    assert c21_sign.value is None
    assert d10_sign.value == Decimal("60")


@pytest.mark.django_db
def test_inactive_signs_are_only_fixed_when_requested():
    sign = create_sign("C21_3", None)
    sign.soft_delete(get_user())

    apply_fixes()
    sign.refresh_from_db()
    assert sign.value is None

    apply_fixes(include_inactive=True)
    sign.refresh_from_db()
    assert sign.value == Decimal("2.1")


@pytest.mark.django_db
def test_plan_fixes_does_not_write_anything():
    sign = create_sign("C21_3", Decimal("2.4"))

    fixes = get_fixes()
    sign.refresh_from_db()

    assert sign.value == Decimal("2.4")
    assert len(fixes) == 1


def read_csv_report(checker, tmp_path, **kwargs):
    """Write a CSV report and return its rows."""
    csv_path = tmp_path / "report.csv"
    checker.write_csv_report(str(csv_path), **kwargs)
    with open(csv_path, encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


@pytest.mark.django_db
def test_csv_report_marks_problems_as_not_fixed_when_fixing_was_not_requested(tmp_path):
    create_sign("C21_3", Decimal("2.4"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    rows = read_csv_report(checker, tmp_path)

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_NOT_REQUESTED
    assert rows[0]["fix"] == ""


@pytest.mark.django_db
def test_csv_report_records_applied_fixes(tmp_path):
    create_sign("C21_3", None)
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user())

    rows = read_csv_report(checker, tmp_path, fixes=fixes)

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_FIXED
    assert rows[0]["fix"] == "C21_3 value no value -> 2.1"


@pytest.mark.django_db
def test_csv_report_records_dry_run_fixes(tmp_path):
    create_sign("C21_3", None)
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user(), dry_run=True)

    rows = read_csv_report(checker, tmp_path, fixes=fixes, dry_run=True)

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_WOULD_BE_FIXED
    assert rows[0]["fix"] == "C21_3 value no value -> 2.1"


@pytest.mark.django_db
def test_csv_report_records_skipped_fixes(tmp_path):
    create_sign("C21", Decimal("2.1"))
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user())

    rows = read_csv_report(checker, tmp_path, fixes=fixes)

    assert rows[0]["fix_status"] == traffic_sign_value_check.FIX_STATUS_SKIPPED
    assert rows[0]["fix"] == "C21 -> C21_3: device type 'C21_3' does not exist"


@pytest.mark.django_db
def test_results_as_dicts_payload_is_json_serializable():
    create_sign("C21_3", Decimal("2.4"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    payload = traffic_sign_value_check.results_as_dicts(checker.results)

    assert json.loads(json.dumps(payload)) == payload


@pytest.mark.django_db
def test_results_as_dicts_converts_decimal_and_uuid_to_strings():
    sign = create_sign("C21_3", Decimal("2.4"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    problem = traffic_sign_value_check.results_as_dicts(checker.results)[0]

    assert problem["id"] == str(sign.id)
    assert problem["value"] == "2.40"
    assert problem["expected_value"] == "2.1"


@pytest.mark.django_db
def test_results_as_dicts_keeps_null_values_as_none():
    create_sign("C21_3", None)
    checker = TrafficSignValueChecker()
    checker.check_signs()

    problem = traffic_sign_value_check.results_as_dicts(checker.results)[0]

    assert problem["value"] is None
    assert problem["error_category"] == traffic_sign_value_check.SUBCODE_MISSING_VALUE


@pytest.mark.django_db
def test_results_as_dicts_uses_the_same_columns_as_the_csv_report():
    create_sign("C21_3", Decimal("2.4"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    problem = traffic_sign_value_check.results_as_dicts(checker.results)[0]

    assert list(problem.keys()) == list(traffic_sign_value_check.CSV_HEADER)


@pytest.mark.django_db
def test_results_as_dicts_without_fixes_is_not_requested():
    create_sign("C21_3", Decimal("2.4"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    problem = traffic_sign_value_check.results_as_dicts(checker.results)[0]

    assert problem["fix_status"] == traffic_sign_value_check.FIX_STATUS_NOT_REQUESTED
    assert problem["fix"] == ""


@pytest.mark.django_db
def test_results_as_dicts_records_applied_fixes():
    create_sign("C21_3", None)
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user())

    problem = traffic_sign_value_check.results_as_dicts(checker.results, fixes)[0]

    assert problem["fix_status"] == traffic_sign_value_check.FIX_STATUS_FIXED
    assert problem["fix"] == "C21_3 value no value -> 2.1"


@pytest.mark.django_db
def test_results_as_dicts_records_dry_run_fixes():
    create_sign("C21_3", None)
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user(), dry_run=True)

    problem = traffic_sign_value_check.results_as_dicts(checker.results, fixes, dry_run=True)[0]

    assert problem["fix_status"] == traffic_sign_value_check.FIX_STATUS_WOULD_BE_FIXED
    assert problem["fix"] == "C21_3 value no value -> 2.1"


@pytest.mark.django_db
def test_results_as_dicts_records_skipped_fixes():
    create_sign("C21", Decimal("2.1"))
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user())

    problem = traffic_sign_value_check.results_as_dicts(checker.results, fixes)[0]

    assert problem["fix_status"] == traffic_sign_value_check.FIX_STATUS_SKIPPED
    assert problem["fix"] == "C21 -> C21_3: device type 'C21_3' does not exist"


@pytest.mark.django_db
def test_get_run_counts_without_fixes():
    create_sign("C21_3", Decimal("2.4"))
    create_sign("C21_4", Decimal("2.3"))
    checker = TrafficSignValueChecker()
    checker.check_signs()

    assert checker.get_run_counts() == {
        "checked_count": 2,
        "problem_count": 1,
        "fixed_count": 0,
        "skipped_fix_count": 0,
    }


@pytest.mark.django_db
def test_get_run_counts_separates_fixed_and_skipped():
    create_sign("C21_3", None)
    create_sign("C21", Decimal("2.5"))
    checker = TrafficSignValueChecker()
    checker.check_signs()
    fixes = checker.apply_fixes(user=get_system_user())

    assert checker.get_run_counts(fixes) == {
        "checked_count": 2,
        "problem_count": 2,
        "fixed_count": 1,
        "skipped_fix_count": 1,
    }


def test_checker_module_does_not_know_about_the_run_info_model():
    """The calling party owns persistence, so the checker must not reference the model."""
    source = Path(traffic_sign_value_check.__file__).read_text()

    assert "TrafficSignValueCheckRunInfo" not in source
