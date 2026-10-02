import re
from typing import Optional

PAATOKSET_DECISION_URL_BASE = "https://paatokset.hel.fi/fi/asia"

_WHITESPACE_PATTERN = re.compile(r"\s+")


def get_plan_decision_url(diary_number: Optional[str]) -> str:
    """Build the paatokset.hel.fi decision URL for a plan's diary number.

    The diary number is stripped of surrounding whitespace and any remaining
    whitespace runs are replaced with a single dash. The original casing is
    preserved, e.g. ``HEL 2024-013184`` becomes
    ``https://paatokset.hel.fi/fi/asia/HEL-2024-013184``.

    Args:
        diary_number (Optional[str]): Diary number of the plan.

    Returns:
        str: The decision URL, or an empty string when no diary number is given.
    """
    if not diary_number or not diary_number.strip():
        return ""

    slug = _WHITESPACE_PATTERN.sub("-", diary_number.strip())
    return f"{PAATOKSET_DECISION_URL_BASE}/{slug}"
