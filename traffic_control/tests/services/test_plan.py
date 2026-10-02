import pytest

from traffic_control.services.plan import get_plan_decision_url


@pytest.mark.parametrize(
    "diary_number,expected",
    (
        ("HEL 2024-013184", "https://paatokset.hel.fi/fi/asia/HEL-2024-013184"),
        ("  HEL 2024-013184  ", "https://paatokset.hel.fi/fi/asia/HEL-2024-013184"),
        ("HEL   2024-013184", "https://paatokset.hel.fi/fi/asia/HEL-2024-013184"),
        ("HEL-2024-013184", "https://paatokset.hel.fi/fi/asia/HEL-2024-013184"),
        ("DN1", "https://paatokset.hel.fi/fi/asia/DN1"),
        ("", ""),
        ("   ", ""),
        (None, ""),
    ),
)
def test__get_plan_decision_url(diary_number, expected):
    assert get_plan_decision_url(diary_number) == expected
