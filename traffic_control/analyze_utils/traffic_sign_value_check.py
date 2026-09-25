"""Checks that TrafficSignReal values are in line with their device type code."""
import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from traffic_control.constants import SignValueFamily, TRAFFIC_SIGN_VALUE_FAMILIES
from traffic_control.models import TrafficControlDeviceType, TrafficSignReal
from traffic_control.services.common import get_lifecycle_queryset
from users.models import User

GENERIC_WITH_SUBCODE_VALUE = "generic_with_subcode_value"
SUBCODE_WRONG_VALUE = "subcode_wrong_value"
SUBCODE_MISSING_VALUE = "subcode_missing_value"

BULK_UPDATE_BATCH_SIZE = 500

# Fix status of a problem in the CSV report.
FIX_STATUS_NOT_REQUESTED = "not_requested"
FIX_STATUS_FIXED = "fixed"
FIX_STATUS_WOULD_BE_FIXED = "would_be_fixed"
FIX_STATUS_SKIPPED = "skipped"

# A sign that carries the wrong value for its own subcode is never corrected automatically, as
# either the value or the device type could be the one that is wrong.
AMBIGUOUS_FIX_REASON = "cannot tell whether the value or the device type is wrong"

CSV_HEADER = [
    "id",
    "device_type_code",
    "generic_code",
    "value",
    "expected_value",
    "matching_subcode",
    "error_category",
    "fix_status",
    "fix",
    "source_name",
    "source_id",
    "admin_url",
]

# Sign id, device type code, value, source name and source id of a single traffic sign real.
SignRow = Tuple[UUID, str, Optional[Decimal], Optional[str], Optional[str]]


@dataclass(frozen=True)
class ValueCheckResult:
    """Single problem found in a traffic sign real's value.

    Attributes:
        sign_id (UUID): Id of the offending TrafficSignReal.
        device_type_code (str): Device type code of the sign.
        generic_code (str): Generic code of the family the device type belongs to.
        value (Optional[Decimal]): Value the sign currently has.
        expected_value (Optional[Decimal]): Value the sign is expected to have, if known.
        matching_subcode (Optional[str]): Subcode whose value a generic code sign is carrying.
        error_category (str): Category of the problem.
        source_name (Optional[str]): Source name of the sign.
        source_id (Optional[str]): Source id of the sign.
    """

    sign_id: UUID
    device_type_code: str
    generic_code: str
    value: Optional[Decimal]
    expected_value: Optional[Decimal]
    matching_subcode: Optional[str]
    error_category: str
    source_name: Optional[str]
    source_id: Optional[str]

    def as_csv_row(self, fix_status: str = FIX_STATUS_NOT_REQUESTED, fix_description: str = "") -> List[str]:
        """Format the result as a CSV row.

        Args:
            fix_status (str): What happened to this problem when fixing was requested.
            fix_description (str): Description of the fix, or of why it was skipped.

        Returns:
            List[str]: Values in the order of CSV_HEADER.
        """
        return [
            str(self.sign_id),
            self.device_type_code,
            self.generic_code,
            "" if self.value is None else str(self.value),
            "" if self.expected_value is None else str(self.expected_value),
            self.matching_subcode or "",
            self.error_category,
            fix_status,
            fix_description,
            self.source_name or "",
            self.source_id or "",
            get_admin_url(self.sign_id),
        ]

    @property
    def description(self) -> str:
        """Human readable description of the problem, including the expected value.

        Returns:
            str: Description of what is wrong with the sign's value.
        """
        value = "no value" if self.value is None else f"value {self.value}"
        if self.error_category == GENERIC_WITH_SUBCODE_VALUE:
            return (
                f"{self.device_type_code} has {value}, which is the expected value of subcode "
                f"{self.matching_subcode}. Expected: any value that is not a subcode value, or device "
                f"type {self.matching_subcode}"
            )

        return f"{self.device_type_code} has {value}, expected value: {self.expected_value}"


@dataclass(frozen=True)
class SignFix:
    """A concrete change that corrects a single value problem.

    At most one change is made: a value fix writes `target_value` into the sign's own value
    column, while a device type fix repoints the sign's device type foreign key at
    `target_device_type_code` and keeps the value as it is. A skipped fix makes no change at all.

    Attributes:
        result (ValueCheckResult): Problem this fix corrects.
        target_value (Optional[Decimal]): Value to write, or None when the value is kept.
        target_device_type_code (Optional[str]): Device type code to move the sign to, or None
            when the device type is kept.
        target_device_type_id (Optional[UUID]): Id of the target device type, None when the
            device type is kept or when it does not exist in the database.
        skipped_reason (Optional[str]): Why the fix cannot be applied, None when it can.
    """

    result: ValueCheckResult
    target_value: Optional[Decimal] = None
    target_device_type_code: Optional[str] = None
    target_device_type_id: Optional[UUID] = None
    skipped_reason: Optional[str] = None

    @property
    def is_skipped(self) -> bool:
        """Whether the fix cannot be applied.

        Returns:
            bool: True when the fix has a skip reason.
        """
        return self.skipped_reason is not None

    @property
    def description(self) -> str:
        """Human readable description of the change the fix makes.

        Returns:
            str: Description of the change, or of why it is skipped.
        """
        if self.skipped_reason is not None:
            target = f" -> {self.target_device_type_code}" if self.target_device_type_code else ""
            return f"{self.result.device_type_code}{target}: {self.skipped_reason}"

        if self.target_device_type_code is not None:
            return (
                f"{self.result.device_type_code} -> {self.target_device_type_code} " f"(value {self.result.value} kept)"
            )

        current = "no value" if self.result.value is None else str(self.result.value)
        return f"{self.result.device_type_code} value {current} -> {self.target_value}"


def _get_fix_columns(fix: Optional["SignFix"], dry_run: bool) -> Tuple[str, str]:
    """Resolve the fix status and description columns of a CSV row.

    Args:
        fix (Optional[SignFix]): Fix planned for the problem, or None when fixing was not
            requested.
        dry_run (bool): Whether the fix was only planned and not written.

    Returns:
        Tuple[str, str]: Fix status and description of the fix.
    """
    if fix is None:
        return FIX_STATUS_NOT_REQUESTED, ""

    if fix.is_skipped:
        return FIX_STATUS_SKIPPED, fix.description

    status = FIX_STATUS_WOULD_BE_FIXED if dry_run else FIX_STATUS_FIXED
    return status, fix.description


def get_admin_url(sign_id: UUID) -> str:
    """Build an admin change URL for a traffic sign real.

    Args:
        sign_id (UUID): Id of the traffic sign real.

    Returns:
        str: Full admin change URL of the sign.
    """
    base_url = getattr(settings, "BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base_url}{reverse('admin:traffic_control_trafficsignreal_change', args=[sign_id])}"


def result_as_dict(result: ValueCheckResult, fix_status: str, fix_description: str) -> Dict[str, Any]:
    """Convert a single problem into a JSON serializable dict.

    `Decimal` and `UUID` values are converted to strings, as neither can be serialized by the
    JSON encoder that `JSONField` uses.

    Args:
        result (ValueCheckResult): Problem to convert.
        fix_status (str): What happened to the problem when fixing was requested.
        fix_description (str): Description of the fix, or of why it was skipped.

    Returns:
        Dict[str, Any]: The problem as plain JSON serializable values.
    """
    return {
        "id": str(result.sign_id),
        "device_type_code": result.device_type_code,
        "generic_code": result.generic_code,
        "value": None if result.value is None else str(result.value),
        "expected_value": None if result.expected_value is None else str(result.expected_value),
        "matching_subcode": result.matching_subcode,
        "error_category": result.error_category,
        "fix_status": fix_status,
        "fix": fix_description,
        "source_name": result.source_name,
        "source_id": result.source_id,
        "admin_url": get_admin_url(result.sign_id),
    }


def results_as_dicts(
    results: List[ValueCheckResult],
    fixes: Optional[List["SignFix"]] = None,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Convert the found problems into a JSON serializable payload.

    The fix status of each problem is resolved the same way as for the CSV report, so that the
    two cannot drift apart.

    Args:
        results (List[ValueCheckResult]): Problems to convert.
        fixes (Optional[List[SignFix]]): Fixes that were planned for the problems, or None when
            fixing was not requested.
        dry_run (bool): Whether the given fixes were only planned and not written.

    Returns:
        List[Dict[str, Any]]: The problems as plain JSON serializable values.
    """
    fixes_by_sign_id = {fix.result.sign_id: fix for fix in fixes or []}
    return [
        result_as_dict(result, *_get_fix_columns(fixes_by_sign_id.get(result.sign_id), dry_run)) for result in results
    ]


def _parse_decimal(value: Any, description: str) -> Decimal:
    """Convert a JSON value into a Decimal.

    Args:
        value (Any): Value from the JSON file, either a string or a number.
        description (str): Description of the value used in the error message.

    Returns:
        Decimal: The value as a Decimal.

    Raises:
        ValueError: If the value cannot be converted into a Decimal.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{description} must be a number or a numeric string, got {value!r}")

    try:
        return Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{description} must be a number or a numeric string, got {value!r}")


def _parse_subcodes(subcodes: Any, generic_code: str) -> Dict[str, Decimal]:
    """Parse the subcodes of a single family definition.

    Args:
        subcodes (Any): Value of the family's "subcodes" key.
        generic_code (str): Generic code of the family, used in error messages.

    Returns:
        Dict[str, Decimal]: Mapping of subcode to its expected value.

    Raises:
        ValueError: If the subcodes are not an object or a subcode value is not numeric.
    """
    if not isinstance(subcodes, dict):
        raise ValueError(f"Family '{generic_code}': 'subcodes' must be an object, got {subcodes!r}")

    return {
        subcode: _parse_decimal(value, f"Family '{generic_code}': value of subcode '{subcode}'")
        for subcode, value in subcodes.items()
    }


def build_family(generic_code: str, definition: Any) -> SignValueFamily:
    """Build a sign value family from a single JSON family definition.

    Args:
        generic_code (str): Generic code of the family, e.g. "C21".
        definition (Any): Family definition with the optional keys "default_value" and "subcodes".

    Returns:
        SignValueFamily: Family built from the definition.

    Raises:
        ValueError: If the definition is not an object or contains invalid values.
    """
    if not isinstance(definition, dict):
        raise ValueError(f"Family '{generic_code}' must be an object, got {definition!r}")

    default_value = definition.get("default_value")
    if default_value is not None:
        default_value = _parse_decimal(default_value, f"Family '{generic_code}': 'default_value'")

    return SignValueFamily(
        generic_code=generic_code,
        default_value=default_value,
        subcodes=_parse_subcodes(definition.get("subcodes", {}), generic_code),
    )


def load_families_from_json(path: str) -> Dict[str, SignValueFamily]:
    """Load extra sign value families from a JSON file.

    The file contains an object keyed by generic code. Each family may define the optional keys
    "default_value" (a number, a numeric string or null) and "subcodes" (an object mapping subcode
    to its expected value).

    Args:
        path (str): Path of the JSON file to read.

    Returns:
        Dict[str, SignValueFamily]: Families by their generic code.

    Raises:
        ValueError: If the file cannot be read, is not valid JSON or contains invalid definitions.
    """
    try:
        with open(path, encoding="utf-8") as json_file:
            content = json.load(json_file)
    except OSError as error:
        raise ValueError(f"Could not read extra families file '{path}': {error}")
    except json.JSONDecodeError as error:
        raise ValueError(f"Extra families file '{path}' is not valid JSON: {error}")

    if not isinstance(content, dict):
        raise ValueError(f"Extra families file '{path}' must contain a JSON object of families")

    return {code: build_family(code, definition) for code, definition in content.items()}


class TrafficSignValueChecker:
    """Checks TrafficSignReal values against the traffic sign code families.

    Signs using a subcode must have exactly the value defined for that subcode. Signs using the generic
    code of a family must not have a value that belongs to any of the family's subcodes, as those signs
    should be using the subcode instead. Nothing is modified by the checker.
    """

    def __init__(
        self,
        codes: Optional[List[str]] = None,
        include_inactive: bool = False,
        extra_families: Optional[Dict[str, SignValueFamily]] = None,
    ) -> None:
        """Initialize the checker.

        Args:
            codes (Optional[List[str]]): Generic codes to limit the check to. All known families are
                checked when None or empty.
            include_inactive (bool): Whether soft-deleted traffic sign reals and signs whose
                lifecycle is not active or temporarily active are checked too.
            extra_families (Optional[Dict[str, SignValueFamily]]): Additional families by their generic
                code. These override built-in families that use the same generic code.

        Raises:
            ValueError: If any of the given codes is not a known generic code.
        """
        self.families = self._select_families(codes, extra_families)
        self.include_inactive = include_inactive
        self.generic_lookup, self.subcode_lookup = self._build_lookups(self.families)
        self.results: List[ValueCheckResult] = []
        self.checked_count = 0

    @staticmethod
    def _select_families(
        codes: Optional[List[str]],
        extra_families: Optional[Dict[str, SignValueFamily]] = None,
    ) -> Dict[str, SignValueFamily]:
        """Select the sign value families to check.

        Args:
            codes (Optional[List[str]]): Generic codes to limit the check to.
            extra_families (Optional[Dict[str, SignValueFamily]]): Additional families that override
                built-in families with the same generic code.

        Returns:
            Dict[str, SignValueFamily]: Selected families by their generic code.

        Raises:
            ValueError: If any of the given codes is not a known generic code.
        """
        known_families = {**TRAFFIC_SIGN_VALUE_FAMILIES, **(extra_families or {})}
        if not codes:
            return known_families

        unknown_codes = sorted(set(codes) - set(known_families))
        if unknown_codes:
            known_codes = ", ".join(sorted(known_families))
            raise ValueError(f"Unknown generic code(s): {', '.join(unknown_codes)}. Known codes: {known_codes}")

        return {code: known_families[code] for code in codes}

    @staticmethod
    def _build_lookups(
        families: Dict[str, SignValueFamily],
    ) -> Tuple[Dict[str, SignValueFamily], Dict[str, Tuple[SignValueFamily, Decimal]]]:
        """Build device type code lookups for the given families.

        Args:
            families (Dict[str, SignValueFamily]): Families to build the lookups from.

        Returns:
            Tuple[Dict[str, SignValueFamily], Dict[str, Tuple[SignValueFamily, Decimal]]]: Mapping of
                generic code to its family and mapping of subcode to its family and expected value.
        """
        generic_lookup: Dict[str, SignValueFamily] = {}
        subcode_lookup: Dict[str, Tuple[SignValueFamily, Decimal]] = {}

        for family in families.values():
            generic_lookup[family.generic_code] = family
            for subcode, expected_value in family.subcodes.items():
                subcode_lookup[subcode] = (family, expected_value)

        return generic_lookup, subcode_lookup

    @property
    def checked_codes(self) -> List[str]:
        """Device type codes that are included in the check.

        Returns:
            List[str]: Generic codes and subcodes of the selected families.
        """
        return list(self.generic_lookup) + list(self.subcode_lookup)

    def get_missing_device_type_codes(self) -> List[str]:
        """Find declared family codes that do not exist as device types.

        Returns:
            List[str]: Sorted codes that have no matching TrafficControlDeviceType row.
        """
        codes = set(self.checked_codes)
        existing_codes = set(TrafficControlDeviceType.objects.filter(code__in=codes).values_list("code", flat=True))
        return sorted(codes - existing_codes)

    def get_signs_queryset(self) -> QuerySet:
        """Build the queryset of traffic sign reals to check.

        By default only signs that are in use are checked, which means both that the sign has
        not been soft-deleted and that its lifecycle is active or temporarily active.

        Returns:
            QuerySet: Traffic sign reals limited to the checked device type codes.
        """
        if self.include_inactive:
            queryset = TrafficSignReal.objects.all()
        else:
            queryset = get_lifecycle_queryset(TrafficSignReal.objects.active())

        return queryset.filter(device_type__code__in=self.checked_codes).order_by("device_type__code")

    def check_signs(self) -> List[ValueCheckResult]:
        """Check all relevant traffic sign reals and store the found problems.

        Returns:
            List[ValueCheckResult]: Problems that were found.
        """
        sign_rows = self.get_signs_queryset().values_list(
            "id", "device_type__code", "value", "source_name", "source_id"
        )

        self.results = []
        self.checked_count = 0
        for sign in sign_rows.iterator():
            self.checked_count += 1
            result = self.check_sign(sign)
            if result is not None:
                self.results.append(result)

        return self.results

    def check_sign(self, sign: SignRow) -> Optional[ValueCheckResult]:
        """Check a single traffic sign real against its device type code family.

        Args:
            sign (SignRow): Sign id, device type code, value, source name and source id.

        Returns:
            Optional[ValueCheckResult]: Result when the sign has a problem, otherwise None.
        """
        code = sign[1]
        family = self.generic_lookup.get(code)
        if family is not None:
            return self._check_generic_sign(sign, family)

        subcode_entry = self.subcode_lookup.get(code)
        if subcode_entry is not None:
            return self._check_subcode_sign(sign, subcode_entry[0], subcode_entry[1])

        return None

    @staticmethod
    def _check_generic_sign(sign: SignRow, family: SignValueFamily) -> Optional[ValueCheckResult]:
        """Check a sign that uses the generic code of a family.

        Args:
            sign (SignRow): Sign id, device type code, value, source name and source id.
            family (SignValueFamily): Family the sign's device type belongs to.

        Returns:
            Optional[ValueCheckResult]: Result when the sign carries a value belonging to one of the
                family's subcodes, otherwise None.
        """
        sign_id, code, value, source_name, source_id = sign
        matching_subcode = next(
            (subcode for subcode, subcode_value in family.subcodes.items() if subcode_value == value),
            None,
        )
        if value is None or matching_subcode is None:
            return None

        return ValueCheckResult(
            sign_id=sign_id,
            device_type_code=code,
            generic_code=family.generic_code,
            value=value,
            expected_value=None,
            matching_subcode=matching_subcode,
            error_category=GENERIC_WITH_SUBCODE_VALUE,
            source_name=source_name,
            source_id=source_id,
        )

    @staticmethod
    def _check_subcode_sign(
        sign: SignRow,
        family: SignValueFamily,
        expected_value: Decimal,
    ) -> Optional[ValueCheckResult]:
        """Check a sign that uses a subcode of a family.

        Args:
            sign (SignRow): Sign id, device type code, value, source name and source id.
            family (SignValueFamily): Family the sign's device type belongs to.
            expected_value (Decimal): Value the subcode is expected to have.

        Returns:
            Optional[ValueCheckResult]: Result when the value is missing or differs from the expected
                value, otherwise None.
        """
        sign_id, code, value, source_name, source_id = sign
        if value is not None and value == expected_value:
            return None

        return ValueCheckResult(
            sign_id=sign_id,
            device_type_code=code,
            generic_code=family.generic_code,
            value=value,
            expected_value=expected_value,
            matching_subcode=None,
            error_category=SUBCODE_MISSING_VALUE if value is None else SUBCODE_WRONG_VALUE,
            source_name=source_name,
            source_id=source_id,
        )

    def _resolve_device_type_ids(self) -> Dict[str, UUID]:
        """Look up the ids of the subcodes that generic code fixes need to move signs to.

        Returns:
            Dict[str, UUID]: Device type id by code, containing only codes that exist.
        """
        wanted_codes = {
            result.matching_subcode
            for result in self.results
            if result.error_category == GENERIC_WITH_SUBCODE_VALUE and result.matching_subcode
        }
        rows = TrafficControlDeviceType.objects.filter(code__in=wanted_codes).values_list("code", "id")
        return dict(rows)

    def _plan_fix(self, result: ValueCheckResult, device_type_ids: Dict[str, UUID]) -> SignFix:
        """Build the fix that corrects a single problem.

        A sign that carries the wrong value for its own subcode is always skipped, as it is not
        possible to tell whether the value or the device type is the one that should be changed.

        Args:
            result (ValueCheckResult): Problem to correct.
            device_type_ids (Dict[str, UUID]): Ids of the existing subcode device types.

        Returns:
            SignFix: The change that corrects the problem, possibly marked as skipped.
        """
        if result.error_category == SUBCODE_WRONG_VALUE:
            return SignFix(result=result, skipped_reason=AMBIGUOUS_FIX_REASON)

        if result.error_category == SUBCODE_MISSING_VALUE:
            return SignFix(result=result, target_value=result.expected_value)

        subcode = result.matching_subcode
        device_type_id = device_type_ids.get(subcode)
        skipped_reason = None if device_type_id else f"device type '{subcode}' does not exist"
        return SignFix(
            result=result,
            target_device_type_code=subcode,
            target_device_type_id=device_type_id,
            skipped_reason=skipped_reason,
        )

    def plan_fixes(self) -> List[SignFix]:
        """Turn the found problems into the changes that would correct them.

        Returns:
            List[SignFix]: One fix per found problem, in the order the problems were found.
        """
        device_type_ids = self._resolve_device_type_ids()
        return [self._plan_fix(result, device_type_ids) for result in self.results]

    def apply_fixes(self, user: User, dry_run: bool = False) -> List[SignFix]:
        """Correct the found problems.

        Args:
            user (User): User to stamp the corrected signs with as their updater.
            dry_run (bool): When True nothing is written and the fixes are only planned.

        Returns:
            List[SignFix]: The planned fixes, including the ones that were skipped.
        """
        fixes = self.plan_fixes()
        applicable_fixes = [fix for fix in fixes if not fix.is_skipped]
        if dry_run or not applicable_fixes:
            return fixes

        with transaction.atomic():
            self._write_fixes(applicable_fixes, user)

        return fixes

    @staticmethod
    def _write_fixes(fixes: List[SignFix], user: User) -> None:
        """Write the given fixes into the database.

        `bulk_update` is used on purpose, as it bypasses `Model.save()` and therefore
        `DecimalValueFromDeviceTypeMixin`, which would otherwise be able to re-derive the very
        value that is being corrected. It also skips the `auto_now` handling of `updated_at`,
        which is why that field is set explicitly.

        Args:
            fixes (List[SignFix]): Fixes that can be applied.
            user (User): User to stamp the corrected signs with as their updater.

        Returns:
            None
        """
        fixes_by_sign_id = {fix.result.sign_id: fix for fix in fixes}
        signs = list(TrafficSignReal.objects.filter(pk__in=fixes_by_sign_id))
        now = timezone.now()

        for sign in signs:
            fix = fixes_by_sign_id[sign.id]
            if fix.target_device_type_code is not None:
                sign.device_type_id = fix.target_device_type_id
            else:
                sign.value = fix.target_value
            sign.updated_by = user
            sign.updated_at = now

        TrafficSignReal.objects.bulk_update(
            signs,
            ["value", "device_type", "updated_by", "updated_at"],
            batch_size=BULK_UPDATE_BATCH_SIZE,
        )

    def get_counts_by(self, key: str) -> Dict[str, int]:
        """Count the found problems grouped by a result attribute.

        Args:
            key (str): Name of the ValueCheckResult attribute to group by.

        Returns:
            Dict[str, int]: Counts by attribute value, ordered by the attribute value.
        """
        counts: Dict[str, int] = {}
        for result in self.results:
            value = getattr(result, key)
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    def get_expected_value(self, code: str) -> Optional[Decimal]:
        """Get the value a device type code is expected to have.

        Args:
            code (str): Device type code.

        Returns:
            Optional[Decimal]: Expected value of a subcode, or None for a generic code or an unknown
                code, as those have no single expected value.
        """
        subcode_entry = self.subcode_lookup.get(code)
        return subcode_entry[1] if subcode_entry is not None else None

    def get_code_summary(self) -> Dict[str, Dict[str, Any]]:
        """Summarize the found problems by device type code, including expected values.

        Returns:
            Dict[str, Dict[str, Any]]: Per device type code the number of problems ("count"), the
                expected value of the code ("expected_value", None for generic codes) and whether the
                code is the generic code of its family ("is_generic").
        """
        summary: Dict[str, Dict[str, Any]] = {}
        for code, count in self.get_counts_by("device_type_code").items():
            summary[code] = {
                "count": count,
                "expected_value": self.get_expected_value(code),
                "is_generic": code in self.generic_lookup,
            }
        return summary

    def get_summary(self) -> Dict[str, Dict[str, int]]:
        """Summarize the found problems.

        Returns:
            Dict[str, Dict[str, int]]: Problem counts by error category, generic code and device type
                code.
        """
        return {
            "error_category": self.get_counts_by("error_category"),
            "generic_code": self.get_counts_by("generic_code"),
            "device_type_code": self.get_counts_by("device_type_code"),
        }

    def get_run_counts(self, fixes: Optional[List[SignFix]] = None) -> Dict[str, int]:
        """Count what the run checked, found and corrected.

        Args:
            fixes (Optional[List[SignFix]]): Fixes that were planned, or None when fixing was
                not requested.

        Returns:
            Dict[str, int]: Number of checked signs ("checked_count"), found problems
                ("problem_count"), corrected problems ("fixed_count") and problems that could
                not be corrected ("skipped_fix_count").
        """
        fixes = fixes or []
        return {
            "checked_count": self.checked_count,
            "problem_count": len(self.results),
            "fixed_count": len([fix for fix in fixes if not fix.is_skipped]),
            "skipped_fix_count": len([fix for fix in fixes if fix.is_skipped]),
        }

    def write_csv_report(
        self,
        path: str,
        fixes: Optional[List[SignFix]] = None,
        dry_run: bool = False,
    ) -> None:
        """Write the found problems into a CSV file.

        When fixes are given, each row also tells what happened to that problem, so that the
        report stays a complete record of both what was found and what was done about it.

        Args:
            path (str): Path of the CSV file to write.
            fixes (Optional[List[SignFix]]): Fixes that were planned for the problems, or None
                when fixing was not requested.
            dry_run (bool): Whether the given fixes were only planned and not written.

        Returns:
            None
        """
        fixes_by_sign_id = {fix.result.sign_id: fix for fix in fixes or []}

        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADER)
            for result in self.results:
                fix = fixes_by_sign_id.get(result.sign_id)
                writer.writerow(result.as_csv_row(*_get_fix_columns(fix, dry_run)))
